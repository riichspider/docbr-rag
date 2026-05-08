"""
OCR para documentos escaneados no docbr-rag.
Usa Tesseract com pré-processamento otimizado para documentos brasileiros.
"""

import cv2
import numpy as np
from PIL import Image
import pytesseract
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
import re

from ..models import TipoDocumento
from ..logging_config import get_logger


# Configurações de OCR para português brasileiro
_OCR_CONFIG = {
    'lang': 'por+eng',  # Português + Inglês
    'config': '--psm 6 --oem 3',  # Modo de bloco, OCR engine
    'dpi': 300,
    'preprocess': True
}

# Padrões OCR para documentos brasileiros
_PADROES_OCR = {
    TipoDocumento.CONTRATO: [
        r"CONTRATO",
        r"CL[AÁ]USULA",
        r"CONTRATANTE",
        r"CONTRATADO",
        r"VIG[ÊE]NCIA",
        r"FORO",
    ],
    TipoDocumento.NFE: [
        r"NOTA\s+FISCAL",
        r"NF-?e",
        r"CHAVE\s+DE\s+ACESSO",
        r"DANFE",
        r"CNPJ",
        r"CFOP",
    ],
    TipoDocumento.BOLETO: [
        r"BOLETO",
        r"BANCO",
        r"C[ÓO]DIGO\s+DE\s+BARRAS",
        r"VENCIMENTO",
        r"NOSSO\s+N[ÚU]MERO",
    ],
    TipoDocumento.LAUDO: [
        r"LAUDO",
        r"PERITO",
        r"CONCLUS[ÃA]O",
        r"METODOLOGIA",
        r"OBJETO\s+DA\s+PER[ÍI]CIA",
    ],
    TipoDocumento.CERTIDAO: [
        r"CERTID[ÃA]O",
        r"CERTIFIC[OA]",
        r"REGISTRO\s+CIVIL",
        r"CART[ÓO]RIO",
        r"MATR[ÍI]CULA",
        r"FOLHA",
    ],
    TipoDocumento.HOLERITE: [
        r"HOLERITE",
        r"CONTRACHEQUE",
        r"INSS",
        r"FGTS",
        r"SAL[ÁA]RIO",
        r"DESCONTOS",
    ],
}


class OCRProcessor:
    """Processador de OCR otimizado para documentos brasileiros."""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Inicializa processador OCR.
        
        Args:
            config: Configurações customizadas de OCR
        """
        self.logger = get_logger("docbr_rag.ocr")
        self.config = config or _OCR_CONFIG
        
        # Verifica se Tesseract está instalado
        try:
            pytesseract.get_tesseract_version()
            self.logger.info("Tesseract detectado e configurado")
        except Exception as e:
            self.logger.error(f"Tesseract não encontrado: {e}")
            raise RuntimeError("Tesseract OCR não está instalado. Instale com: pip install pytesseract")
    
    def preprocess_image(self, image_path: str | Path) -> np.ndarray:
        """
        Pré-processa imagem para melhor OCR.
        
        Args:
            image_path: Caminho da imagem
            
        Returns:
            Imagem pré-processada como array numpy
        """
        try:
            # Carrega imagem
            img = cv2.imread(str(image_path))
            if img is None:
                raise ValueError(f"Não foi possível carregar imagem: {image_path}")
            
            # Converte para grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Aumenta contraste
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            
            # Redução de ruído
            denoised = cv2.fastNlMeansDenoising(enhanced, h=10)
            
            # Binarização adaptativa
            binary = cv2.adaptiveThreshold(
                denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2
            )
            
            # Morfologia para limpar artefatos
            kernel = np.ones((2, 2), np.uint8)
            cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            
            self.logger.debug(f"Imagem {image_path.name} pré-processada")
            return cleaned
            
        except Exception as e:
            self.logger.error(f"Erro no pré-processamento: {e}")
            raise
    
    def extract_text_from_image(self, image_path: str | Path) -> str:
        """
        Extrai texto de uma imagem usando OCR.
        
        Args:
            image_path: Caminho da imagem
            
        Returns:
            Texto extraído
        """
        try:
            if self.config['preprocess']:
                # Pré-processa imagem
                processed_img = self.preprocess_image(image_path)
                # Converte para PIL Image
                pil_img = Image.fromarray(processed_img)
            else:
                # Usa imagem original
                pil_img = Image.open(image_path)
            
            # Configurações específicas para português
            custom_config = r'--oem 3 --psm 6 -c preserve_interword_spaces=1'
            
            # Extrai texto
            text = pytesseract.image_to_string(
                pil_img,
                lang=self.config['lang'],
                config=custom_config
            )
            
            # Limpa texto
            cleaned_text = self._clean_ocr_text(text)
            
            self.logger.debug(f"Extraído {len(cleaned_text)} caracteres de {image_path.name}")
            return cleaned_text
            
        except Exception as e:
            self.logger.error(f"Erro na extração OCR de {image_path}: {e}")
            return ""
    
    def extract_text_from_pdf_scanned(self, pdf_path: str | Path) -> List[Tuple[int, str]]:
        """
        Extrai texto de PDF escaneado usando OCR.
        
        Args:
            pdf_path: Caminho para o PDF
            
        Returns:
            Lista de tuplas (número_página, texto)
        """
        try:
            import fitz  # PyMuPDF
            
            paginas = []
            doc = fitz.open(str(pdf_path))
            
            self.logger.info(f"Processando PDF escaneado: {pdf_path.name}")
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Converte página para imagem
                pix = page.get_pixmap(matrix=fitz.Matrix(_dpi=self.config['dpi']))
                img_data = pix.tobytes("png")
                
                # Salva imagem temporária
                temp_img_path = Path(f"temp_page_{page_num}.png")
                with open(temp_img_path, "wb") as f:
                    f.write(img_data)
                
                try:
                    # Extrai texto com OCR
                    text = self.extract_text_from_image(temp_img_path)
                    
                    if text.strip():
                        paginas.append((page_num + 1, text))
                        self.logger.debug(f"Página {page_num + 1}: {len(text)} caracteres")
                
                finally:
                    # Remove imagem temporária
                    if temp_img_path.exists():
                        temp_img_path.unlink()
            
            doc.close()
            self.logger.info(f"Extraídas {len(paginas)} páginas com OCR")
            return paginas
            
        except ImportError:
            self.logger.error("PyMuPDF não encontrado. Instale com: pip install pymupdf")
            raise
        except Exception as e:
            self.logger.error(f"Erro no OCR do PDF {pdf_path}: {e}")
            raise
    
    def detectar_tipo_ocr(self, texto: str) -> TipoDocumento:
        """
        Detecta tipo de documento usando texto extraído por OCR.
        
        Args:
            texto: Texto extraído por OCR
            
        Returns:
            Tipo de documento detectado
        """
        texto_upper = texto.upper()
        pontuacao = {tipo: 0 for tipo in TipoDocumento}
        
        # Usa padrões específicos para OCR (mais tolerantes)
        padroes_ocr = {
            TipoDocumento.CONTRATO: [
                r"CONTRATO",
                r"CL[AÁ]USULA",
                r"CONTRATANTE",
                r"VIG[ÊE]NCIA",
            ],
            TipoDocumento.NFE: [
                r"NOTA\s+FISCAL",
                r"CHAVE\s+DE\s+ACESSO",
                r"CNPJ",
            ],
            # ... outros tipos
        }
        
        for tipo, padroes in padroes_ocr.items():
            for padrao in padroes:
                if re.search(padrao, texto_upper):
                    pontuacao[tipo] += 1
        
        melhor_tipo = max(pontuacao, key=pontuacao.get)
        if pontuacao[melhor_tipo] == 0:
            return TipoDocumento.DESCONHECIDO
        
        return melhor_tipo
    
    def _clean_ocr_text(self, text: str) -> str:
        """
        Limpa texto extraído por OCR.
        
        Args:
            text: Texto bruto do OCR
            
        Returns:
            Texto limpo
        """
        # Remove múltiplos espaços
        text = re.sub(r' +', ' ', text)
        
        # Corrige erros comuns de OCR em português
        corrections = {
            r'Cl[aá]usula': 'Cláusula',
            r'Vig[eê]ncia': 'Vigência',
            r'For[oó]': 'Foro',
            r'CNPJ': 'CNPJ',
            r'N[oó]mero': 'Número',
            r'Vencimento': 'Vencimento',
            r'Contratante': 'Contratante',
            r'Contratado': 'Contratado',
        }
        
        for error, correction in corrections.items():
            text = re.sub(error, correction, text, flags=re.IGNORECASE)
        
        # Remove caracteres especiais indesejados
        text = re.sub(r'[^\w\s\-\.,;:!?/()@#$%&*+=\[\]{}]', '', text)
        
        # Normaliza espaços em pontuação
        text = re.sub(r'\s+([.,;:!?])', r'\1', text)
        text = re.sub(r'([.,;:!?])\s+', r'\1 ', text)
        
        return text.strip()
    
    def get_ocr_confidence(self, image_path: str | Path) -> float:
        """
        Obtém confiança do OCR para uma imagem.
        
        Args:
            image_path: Caminho da imagem
            
        Returns:
            Nível de confiança (0-1)
        """
        try:
            img = Image.open(image_path)
            
            # Obtém dados do OCR com confiança
            data = pytesseract.image_to_data(
                img, 
                lang=self.config['lang'],
                output_type=pytesseract.Output.DICT
            )
            
            # Calcula confiança média
            confidences = [item['conf'] for item in data['text'] if item['conf'] > 0]
            
            if confidences:
                return sum(confidences) / len(confidences)
            else:
                return 0.0
                
        except Exception as e:
            self.logger.error(f"Erro ao obter confiança OCR: {e}")
            return 0.0


def extrair_texto_ocr(caminho: str | Path) -> List[Tuple[int, str]]:
    """
    Função principal para extração de texto com OCR.
    
    Args:
        caminho: Caminho para o documento (imagem ou PDF)
        
    Returns:
        Lista de tuplas (número_página, texto)
    """
    caminho = Path(caminho)
    ocr = OCRProcessor()
    
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")
    
    # Verifica se é PDF ou imagem
    if caminho.suffix.lower() == '.pdf':
        # PDF escaneado
        return ocr.extract_text_from_pdf_scanned(caminho)
    elif caminho.suffix.lower() in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
        # Imagem única
        text = ocr.extract_text_from_image(caminho)
        return [(1, text)] if text.strip() else []
    else:
        raise ValueError(f"Formato não suportado para OCR: {caminho.suffix}")


def detectar_tipo_ocr(texto: str) -> TipoDocumento:
    """
    Detecta tipo de documento usando texto extraído por OCR.
    
    Args:
        texto: Texto extraído por OCR
        
    Returns:
        Tipo de documento detectado
    """
    ocr = OCRProcessor()
    return ocr.detectar_tipo_ocr(texto)


def preprocessar_documento_para_ocr(
    caminho: str | Path,
    output_dir: str | Path
) -> List[str]:
    """
    Pré-processa documento para melhor OCR.
    
    Args:
        caminho: Caminho do documento original
        output_dir: Diretório de saída
        
    Returns:
        Lista de caminhos das imagens pré-processadas
    """
    caminho = Path(caminho)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    ocr = OCRProcessor()
    processed_images = []
    
    if caminho.suffix.lower() == '.pdf':
        # Processa cada página do PDF
        try:
            import fitz
            doc = fitz.open(str(caminho))
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Converte para imagem de alta resolução
                pix = page.get_pixmap(matrix=fitz.Matrix(300, 300))
                img_path = output_dir / f"page_{page_num + 1:03d}.png"
                pix.save(img_path)
                
                processed_images.append(str(img_path))
            
            doc.close()
            
        except ImportError:
            raise RuntimeError("PyMuPDF necessário para pré-processamento de PDF")
    
    elif caminho.suffix.lower() in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
        # Processa imagem única
        processed_img = output_dir / f"processed_{caminho.name}"
        
        # Aplica pré-processamento
        processed_array = ocr.preprocess_image(caminho)
        processed_pil = Image.fromarray(processed_array)
        processed_pil.save(processed_img)
        
        processed_images.append(str(processed_img))
    
    return processed_images
