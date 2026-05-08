"""
Extrator de texto de documentos TXT brasileiros.
Suporta encoding automático e limpeza de artefatos.
"""

import re
import chardet
from pathlib import Path
from typing import List, Tuple

from ..models import TipoDocumento


# Padrões específicos para TXT brasileiros
_PADROES_TIPO_TXT = {
    TipoDocumento.CONTRATO: [
        r"CONTRATO\s+(DE|SOCIAL|PARTICULAR|DE PRESTAÇÃO)",
        r"CONTRATANTE",
        r"CONTRATADO",
        r"CLÁUSULA\s+\w+",
        r"FORO",
        r"VIGÊNCIA",
        r"MULTA\s+CONTRATUAL",
    ],
    TipoDocumento.NFE: [
        r"NOTA\s+FISCAL\s+ELETR[ÔO]NICA",
        r"NF-?e",
        r"CHAVE\s+DE\s+ACESSO",
        r"DANFE",
        r"CNPJ",
        r"CFOP",
        r"VALOR\s+TOTAL",
    ],
    TipoDocumento.BOLETO: [
        r"BOLETO",
        r"BANCO\s+\w+\s+S\.?A\.?",
        r"C[ÓO]DIGO\s+DE\s+BARRAS",
        r"NOSSO\s+N[ÚU]MERO",
        r"VENCIMENTO",
        r"DATA\s+DE\s+VENCIMENTO",
        r"VALOR\s+DO\s+DOCUMENTO",
    ],
    TipoDocumento.LAUDO: [
        r"LAUDO\s+(T[ÉE]CNICO|M[ÉE]DICO|PERICIAL)",
        r"PERITO",
        r"CONCLUS[ÃA]O",
        r"OBJETO\s+DA\s+PER[ÍI]CIA",
        r"METODOLOGIA",
        r"AN[ÁA]LISE",
    ],
    TipoDocumento.CERTIDAO: [
        r"CERTID[ÃA]O",
        r"CERTIFIC[OA]",
        r"REGISTRO\s+CIVIL",
        r"CART[ÓO]RIO",
        r"MATR[ÍI]CULA",
        r"LIVRO\s+DE\s+REGISTRO",
        r"FOLHA",
    ],
    TipoDocumento.HOLERITE: [
        r"HOLERITE",
        r"CONTRACHEQUE",
        r"RECIBO\s+DE\s+PAGAMENTO",
        r"INSS",
        r"FGTS",
        r"SAL[ÁA]RIO\s+BASE",
        r"DESCONTOS",
        r"LIQUIDO",
    ],
}


def detectar_tipo_txt(texto: str) -> TipoDocumento:
    """
    Detecta o tipo de documento brasileiro com base no conteúdo TXT.

    Args:
        texto: Texto extraído do documento

    Returns:
        TipoDocumento identificado ou DESCONHECIDO
    """
    texto_upper = texto.upper()
    pontuacao = {tipo: 0 for tipo in TipoDocumento}

    for tipo, padroes in _PADROES_TIPO_TXT.items():
        for padrao in padroes:
            if re.search(padrao, texto_upper):
                pontuacao[tipo] += 1

    melhor_tipo = max(pontuacao, key=pontuacao.get)
    if pontuacao[melhor_tipo] == 0:
        return TipoDocumento.DESCONHECIDO

    return melhor_tipo


def extrair_texto_txt(caminho: str | Path) -> List[Tuple[int, str]]:
    """
    Extrai texto de um arquivo TXT com detecção automática de encoding.

    Args:
        caminho: Caminho para o arquivo TXT

    Returns:
        Lista de tuplas (numero_secao, texto)
    """
    caminho = Path(caminho)
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")
    if not caminho.suffix.lower() == ".txt":
        raise ValueError(f"Arquivo deve ser TXT: {caminho}")

    try:
        # Detecta encoding automaticamente
        encoding = _detectar_encoding(caminho)

        # Lê o arquivo com encoding detectado
        with open(caminho, 'r', encoding=encoding, errors='replace') as f:
            conteudo = f.read()

        # Limpa o texto
        conteudo_limpo = _limpar_texto_txt(conteudo)

        # Divide em seções lógicas
        secoes = _dividir_em_secoes(conteudo_limpo)

        return [(i, secao.strip()) for i, secao in enumerate(secoes, 1) if secao.strip()]

    except Exception as e:
        raise RuntimeError(
            f"Não foi possível extrair texto do TXT: {e}") from e


def extrair_metadados_txt(caminho: str | Path) -> dict:
    """
    Extrai metadados do arquivo TXT.

    Args:
        caminho: Caminho para o arquivo TXT

    Returns:
        Dicionário com metadados
    """
    caminho = Path(caminho)

    try:
        # Detecta encoding
        encoding = _detectar_encoding(caminho)

        # Lê o arquivo
        with open(caminho, 'r', encoding=encoding) as f:
            conteudo = f.read()

        # Metadados básicos
        metadados = {
            "arquivo": caminho.name,
            "tamanho": caminho.stat().st_size,
            "encoding": encoding,
            "linhas": len(conteudo.splitlines()),
            "caracteres": len(conteudo),
            "palavras": len(conteudo.split()),
        }

        # Detecta estrutura do documento
        metadados.update(_analisar_estrutura_txt(conteudo))

        # Extrai informações específicas por tipo
        tipo = detectar_tipo_txt(conteudo)
        if tipo != TipoDocumento.DESCONHECIDO:
            metadados.update(_extrair_info_tipo_txt(conteudo, tipo))

        return metadados

    except Exception as e:
        return {"erro": f"Erro ao extrair metadados: {e}"}


def _detectar_encoding(caminho: Path) -> str:
    """
    Detecta encoding do arquivo TXT.

    Args:
        caminho: Caminho para o arquivo

    Returns:
        String com o encoding detectado
    """
    # Tenta detectar encoding com chardet
    try:
        with open(caminho, 'rb') as f:
            raw_data = f.read(10000)  # Lê primeiros 10KB para detecção
            resultado = chardet.detect(raw_data)
            encoding = resultado['encoding']

            # Valida encoding comum para documentos brasileiros
            if encoding and encoding.lower() in ['utf-8', 'utf-16', 'iso-8859-1', 'cp1252']:
                return encoding
    except Exception:
        pass

    # Fallback: tenta encodings comuns
    encodings_comuns = ['utf-8', 'iso-8859-1', 'cp1252', 'utf-16']

    for encoding in encodings_comuns:
        try:
            with open(caminho, 'r', encoding=encoding) as f:
                f.read(1000)  # Tenta ler um pouco
            return encoding
        except UnicodeDecodeError:
            continue

    # Último recurso
    return 'utf-8'


def _dividir_em_secoes(texto: str) -> List[str]:
    """
    Divide o texto em seções lógicas baseado em padrões brasileiros.

    Args:
        texto: Texto completo do documento

    Returns:
        Lista de seções de texto
    """
    # Padrões de separação de seções
    padroes_separacao = [
        r"(?=CLÁUSULA\s+\w+)",              # Cláusulas
        r"(?=ARTIGO\s+\d+)",                 # Artigos
        r"(?=§\s*\d+)",                     # Parágrafos
        r"(?=\d+\.\d+\s+[A-Z])",           # Seções numeradas
        r"(?=\n[A-Z\s]{15,}\n)",           # Títulos em maiúsculas
        r"(?=CONSIDERANDO)",                 # Considerandos
        r"(?=ONDE\s+)",                      # Onde (documentos legais)
        r"(?=PARTE\s+)",                     # Partes
        r"(?=DO\s+)",                        # Seções com "DO"
    ]

    # Tenta separar por padrões específicos
    for padrao in padroes_separacao:
        partes = re.split(padrao, texto, flags=re.MULTILINE | re.IGNORECASE)
        if len(partes) > 1:
            return [p.strip() for p in partes if p.strip()]

    # Se não encontrar padrões específicos, divide por parágrafos duplos
    secoes = re.split(r'\n\s*\n\s*\n', texto)
    return [s.strip() for s in secoes if s.strip()]


def _analisar_estrutura_txt(texto: str) -> dict:
    """
    Analisa a estrutura do texto TXT.

    Args:
        texto: Texto do documento

    Returns:
        Dicionário com informações de estrutura
    """
    linhas = texto.splitlines()

    estrutura = {
        "tem_numeracao": False,
        "tem_titulos_maiusculos": False,
        "tem_data_documento": False,
        "tem_valores_monetarios": False,
        "tem_cnpj_cpf": False,
        "paragrafos_curto": 0,
        "paragrafos_longo": 0,
    }

    # Verifica numeração
    for linha in linhas[:20]:  # Verifica primeiras 20 linhas
        if re.match(r'^\d+\.', linha.strip()):
            estrutura["tem_numeracao"] = True
            break

    # Verifica títulos em maiúsculas
    for linha in linhas:
        if len(linha.strip()) > 15 and linha.strip().isupper():
            estrutura["tem_titulos_maiusculos"] = True
            break

    # Verifica datas
    datas = re.findall(r'\d{2}[/-]\d{2}[/-]\d{2,4}', texto)
    if datas:
        estrutura["tem_data_documento"] = True

    # Verifica valores monetários
    valores = re.findall(r'R?\$\s*\d{1,3}(?:\.\d{3})*,\d{2}', texto)
    if valores:
        estrutura["tem_valores_monetarios"] = True

    # Verifica CNPJ/CPF
    cnpj_cpf = re.findall(r'\d{2}\.?\d{3}\.?\d{3}[\/-]?\d{4}[-]?\d{2}', texto)
    if cnpj_cpf:
        estrutura["tem_cnpj_cpf"] = True

    # Analisa tamanho dos parágrafos
    for linha in linhas:
        linha_limpa = linha.strip()
        if linha_limpa:
            if len(linha_limpa) < 100:
                estrutura["paragrafos_curto"] += 1
            else:
                estrutura["paragrafos_longo"] += 1

    return estrutura


def _extrair_info_tipo_txt(texto: str, tipo: TipoDocumento) -> dict:
    """
    Extrai informações específicas baseadas no tipo de documento.

    Args:
        texto: Texto do documento
        tipo: Tipo detectado do documento

    Returns:
        Dicionário com informações específicas
    """
    info = {"tipo_detectado": tipo.value}

    if tipo == TipoDocumento.CONTRATO:
        # Extrai partes do contrato
        partes = re.findall(
            r'CONTRATANTE[:\s]*\n*(.*?)(?=CONTRATADO|$)', texto, re.DOTALL)
        if partes:
            info["contratante"] = partes[0].strip()

        partes = re.findall(
            r'CONTRATADO[:\s]*\n*(.*?)(?=CLÁUSULA|$)', texto, re.DOTALL)
        if partes:
            info["contratado"] = partes[0].strip()

        # Extrai vigência
        vigencia = re.findall(
            r'VIGÊNCIA[:\s]*\n*(.*?)(?=CLÁUSULA|$)', texto, re.DOTALL)
        if vigencia:
            info["vigencia"] = vigencia[0].strip()

    elif tipo == TipoDocumento.NFE:
        # Extrai CNPJ
        cnpj = re.findall(
            r'CNPJ[:\s]*\n*(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})', texto)
        if cnpj:
            info["cnpj_emitente"] = cnpj[0]

        # Extrai valor total
        valor = re.findall(
            r'VALOR\s+TOTAL[:\s]*\n*R?\$?\s*(\d{1,3}(?:\.\d{3})*,\d{2})', texto)
        if valor:
            info["valor_total"] = valor[0]

    elif tipo == TipoDocumento.BOLETO:
        # Extrai dados bancários
        banco = re.findall(
            r'BANCO[:\s]*\n*(.*?)(?=CÓDIGO|$)', texto, re.DOTALL)
        if banco:
            info["banco"] = banco[0].strip()

        # Extrai vencimento
        venc = re.findall(
            r'VE[NC]IMENTO[:\s]*\n*(\d{2}[/-]\d{2}[/-]\d{2,4})', texto)
        if venc:
            info["vencimento"] = venc[0]

    elif tipo == TipoDocumento.HOLERITE:
        # Extrai salário base
        salario = re.findall(
            r'SAL[ÁA]RIO\s+BASE[:\s]*\n*R?\$?\s*(\d{1,3}(?:\.\d{3})*,\d{2})', texto)
        if salario:
            info["salario_base"] = salario[0]

        # Extrai INSS
        inss = re.findall(
            r'INSS[:\s]*\n*R?\$?\s*(\d{1,3}(?:\.\d{3})*,\d{2})', texto)
        if inss:
            info["inss"] = inss[0]

    return info


def _limpar_texto_txt(texto: str) -> str:
    """
    Limpa artefatos comuns em TXT brasileiros.

    Args:
        texto: Texto bruto

    Returns:
        Texto limpo
    """
    # Remove BOM (Byte Order Mark)
    texto = texto.replace('\ufeff', '')

    # Normaliza quebras de linha
    texto = texto.replace('\r\n', '\n').replace('\r', '\n')

    # Remove múltiplos espaços
    texto = re.sub(r' {2,}', ' ', texto)

    # Remove múltiplas quebras de linha
    texto = re.sub(r'\n{3,}', '\n\n', texto)

    # Remove espaços no início/fim das linhas
    linhas = texto.split('\n')
    linhas = [linha.strip() for linha in linhas]
    texto = '\n'.join(linhas)

    # Remove caracteres de controle exceto quebra de linha
    texto = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', texto)

    # Corrige aspas e apóstrofes
    texto = texto.replace(""", '"').replace(""", '"')
    texto = texto.replace("'", "'").replace("'", "'")

    # Remove espaços extras ao redor de pontuação
    texto = re.sub(r'\s+([.,;:!?)])', r'\1', texto)
    texto = re.sub(r'([.,;:!?)\s+', r'\1', texto)

    return texto.strip()
