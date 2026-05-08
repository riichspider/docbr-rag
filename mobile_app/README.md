# App Mobile docbr-rag

Aplicação mobile React Native para consulta de documentos brasileiros via RAG.

## 🚀 Funcionalidades

### Principais
- ✅ Consulta de documentos por voz e texto
- ✅ Upload e indexação de arquivos
- ✅ Histórico de consultas offline
- ✅ Modo offline para consulta local
- ✅ Interface otimizada para documentos BR

### Específicas para Documentos Brasileiros
- 📄 **Tipos Suportados**: Contratos, NF-e, Boletos, Laudos, Certidões, Holerites
- 🎯 **Busca Inteligente**: Reconhece termos específicos (CNPJ, FORO, etc.)
- 📊 **Analytics Local**: Estatísticas de uso offline
- 🔍 **Filtros Avançados**: Por tipo, data, valor, etc.

## 📱 Tecnologias

- **Framework**: React Native 0.72+
- **State Management**: Redux Toolkit
- **Navigation**: React Navigation 6
- **Storage**: SQLite + AsyncStorage
- **Voice**: React Native Voice
- **Camera**: React Native Image Picker
- **OCR**: Tesseract (via módulo nativo)
- **UI**: NativeBase + React Native Vector Icons

## 🏗️ Estrutura do Projeto

```
mobile_app/
├── src/
│   ├── components/          # Componentes reutilizáveis
│   │   ├── SearchBar/      # Barra de busca com voz
│   │   ├── DocumentCard/   # Card de documento
│   │   ├── FilterModal/    # Modal de filtros
│   │   └── VoiceButton/    # Botão de ativação por voz
│   ├── screens/            # Telas do app
│   │   ├── HomeScreen/     # Tela principal
│   │   ├── SearchScreen/    # Tela de busca
│   │   ├── UploadScreen/    # Tela de upload
│   │   ├── HistoryScreen/   # Tela de histórico
│   │   └── SettingsScreen/  # Tela de configurações
│   ├── services/          # Serviços de API
│   │   ├── apiService/     # Comunicação com backend
│   │   ├── voiceService/    # Processamento de voz
│   │   ├── storageService/  # Armazenamento local
│   │   └── ocrService/     # OCR de documentos
│   ├── store/             # Redux store
│   ├── utils/             # Utilitários
│   └── types/             # TypeScript types
├── android/               # Config Android
├── ios/                   # Config iOS
└── docs/                  # Documentação
```

## 📋 Requisitos

### Desenvolvimento
- Node.js 18+
- React Native CLI
- Android Studio (Android)
- Xcode (iOS)
- Emuladores/simuladores

### Runtime
- Android 8.0+ (API 26+)
- iOS 12.0+
- 2GB+ RAM recomendado
- 500MB+ armazenamento

## 🔧 Instalação e Execução

### Clone do Projeto
```bash
git clone https://github.com/seu-usuario/docbr-rag-mobile.git
cd docbr-rag-mobile
```

### Dependências
```bash
# Instala dependências
npm install

# iOS
cd ios && pod install && cd ..

# Android
npx react-native run-android
```

### Execução em Desenvolvimento
```bash
# Iniciar Metro bundler
npx react-native start

# Android
npx react-native run-android

# iOS
npx react-native run-ios
```

## 🎯 Funcionalidades Detalhadas

### 1. Busca por Voz
```typescript
// Exemplo de uso
const startVoiceSearch = () => {
  VoiceService.startListening({
    language: 'pt-BR',
    onResult: (transcript) => {
      setSearchQuery(transcript);
      performSearch(transcript);
    },
    onError: (error) => {
      showError('Erro na transcrição de voz');
    }
  });
};
```

### 2. Upload de Documentos
```typescript
// Upload com progresso
const uploadDocument = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  try {
    const result = await ApiService.upload('/indexar', formData, {
      onUploadProgress: (progress) => {
        setUploadProgress(progress);
      }
    });
    
    showSuccess('Documento indexado com sucesso!');
    refreshDocuments();
  } catch (error) {
    showError('Erro no upload: ' + error.message);
  }
};
```

### 3. Filtros Avançados
```typescript
// Filtros específicos para BR
const brFilters = {
  tipoDocumento: [
    { label: 'Contrato', value: 'contrato' },
    { label: 'Nota Fiscal', value: 'nfe' },
    { label: 'Boleto', value: 'boleto' },
    { label: 'Laudo', value: 'laudo' },
    { label: 'Certidão', value: 'certidao' },
    { label: 'Holerite', value: 'holerite' }
  ],
  periodo: [
    { label: 'Últimos 7 dias', value: '7d' },
    { label: 'Últimos 30 dias', value: '30d' },
    { label: 'Último ano', value: '1y' }
  ],
  valores: {
    min: 0,
    max: 100000,
    step: 100,
    label: 'Valor (R$)'
  }
};
```

### 4. Offline Mode
```typescript
// Cache de consultas offline
const enableOfflineMode = async () => {
  const cachedQueries = await StorageService.getCachedQueries();
  const cachedDocuments = await StorageService.getCachedDocuments();
  
  // Usa busca local quando offline
  if (!isOnline()) {
    performLocalSearch(cachedQueries, cachedDocuments);
  }
};
```

## 🔒 Segurança

### Autenticação
- Token JWT com refresh
- Biometria (Face ID / Touch ID)
- PIN numérico opcional

### Criptografia
- AES-256 para dados sensíveis
- Secure storage para chaves de API
- Certificado pinning para HTTPS

### Privacidade
- Dados processados localmente
- Opção de apagar dados do dispositivo
- Política de privacidade integrada

## 📊 Analytics Offline

### Métricas Coletadas
- Consultas realizadas
- Tipos de documentos mais buscados
- Tempo médio de resposta
- Taxa de sucesso das buscas
- Uso de funcionalidades

### Dashboard Local
```typescript
const AnalyticsDashboard = () => {
  const [metrics, setMetrics] = useState(null);
  
  useEffect(() => {
    loadLocalMetrics().then(setMetrics);
  }, []);
  
  return (
    <ScrollView>
      <Text style={styles.title}>📊 Uso do App</Text>
      
      <View style={styles.metricCard}>
        <Text>Consultas: {metrics?.totalQueries}</Text>
        <Text>Documentos: {metrics?.totalDocuments}</Text>
      </View>
      
      <BarChart
        data={metrics?.queryTypes}
        title="Tipos de Consulta"
      />
    </ScrollView>
  );
};
```

## 🌐 Integração com Backend

### API Service
```typescript
class ApiService {
  private static BASE_URL = 'https://api.docbr-rag.com/v1';
  
  static async search(query: string, filters?: SearchFilters) {
    const response = await fetch(`${this.BASE_URL}/search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${await this.getToken()}`
      },
      body: JSON.stringify({ query, filters })
    });
    
    return response.json();
  }
  
  static async uploadDocument(file: File, options?: UploadOptions) {
    // Implementação com upload em partes
  }
  
  static async getDocumentHistory() {
    // Histórico de documentos indexados
  }
}
```

### Sincronização
```typescript
// Sincronização inteligente
const syncData = async () => {
  if (isOnline()) {
    // Sincroniza apenas dados modificados
    const localChanges = await StorageService.getPendingChanges();
    
    for (const change of localChanges) {
      try {
        await ApiService.syncChange(change);
        await StorageService.markAsSynced(change.id);
      } catch (error) {
        await StorageService.markAsFailed(change.id, error);
      }
    }
  }
};
```

## 🧪 Testes

### Testes Unitários
```bash
# Testes de componentes
npm test -- --watch

# Testes de serviços
npm run test:services

# Testes de integração
npm run test:integration
```

### Testes E2E
```bash
# Android
npm run test:e2e:android

# iOS
npm run test:e2e:ios

# Cross-platform
npm run test:e2e
```

## 📦 Build e Deploy

### Build para Produção
```bash
# Android
cd android && ./gradlew assembleRelease

# iOS
cd ios && xcodebuild -workspace docbr-rag.xcworkspace \
  -scheme docbr-rag \
  -configuration Release
```

### Publicação nas Stores
```bash
# Google Play Store
npm run deploy:playstore

# Apple App Store
npm run deploy:appstore
```

## 🔧 Configuração

### Variáveis de Ambiente
```bash
# .env
API_BASE_URL=https://api.docbr-rag.com/v1
ENABLE_OFFLINE_MODE=true
ENABLE_VOICE_RECOGNITION=true
ENABLE_BIOMETRIC_AUTH=true
```

### Configuração Específica
```typescript
// src/config/index.ts
export const config = {
  api: {
    baseURL: process.env.API_BASE_URL,
    timeout: 30000,
    retryAttempts: 3
  },
  voice: {
    language: 'pt-BR',
    continuous: false,
    maxDuration: 30000
  },
  offline: {
    maxCacheSize: 100,
    syncInterval: 300000 // 5 minutos
  },
  security: {
    sessionTimeout: 3600000, // 1 hora
    maxFailedAttempts: 3
  }
};
```

## 📱 Design System

### Cores
```typescript
export const colors = {
  primary: '#2E7D32',      // Verde brasileiro
  secondary: '#0097A7',    // Azul
  accent: '#FFDF00',        // Amarelo
  background: '#FFFFFF',
  text: '#212121',
  error: '#D32F2F',
  success: '#388E3C'
};
```

### Tipografia
```typescript
export const typography = {
  fontFamily: {
    primary: 'Roboto-Regular',
    medium: 'Roboto-Medium',
    bold: 'Roboto-Bold'
  },
  fontSize: {
    xs: 12,
    sm: 14,
    md: 16,
    lg: 18,
    xl: 20
  }
};
```

## 🚀 Roadmap Futuro

### Versão 2.0
- [ ] Modo colaborativo (compartilhamento)
- [ ] Anotações em documentos
- [ ] Exportação em múltiplos formatos
- [ ] Widget para home screen
- [ ] Suporte a tablets

### Versão 3.0
- [ ] IA para sugestão de busca
- [ ] Reconhecimento de escrita manual
- [ ] Integração com sistemas legados
- [ ] API GraphQL
- [ ] Real-time sync

## 🤝 Contribuição

### Como Contribuir
1. Fork do repositório
2. Branch feature/nova-funcionalidade
3. Desenvolvimento com testes
4. Pull Request com template

### Padrões de Código
- TypeScript strict
- ESLint + Prettier
- Husky para pre-commit
- 100% de cobertura em novas funcionalidades

## 📄 Licença

MIT License - Ver arquivo LICENSE para detalhes.

---

## 👈 Suporte

- **Email**: mobile@docbr-rag.com
- **Discord**: Comunidade de desenvolvedores
- **Issues**: GitHub Issues
- **Wiki**: Documentação completa

---

**Desenvolvido com ❤️ para o ecossistema brasileiro de documentos!**
