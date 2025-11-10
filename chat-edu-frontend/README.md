# Chat Edu Frontend

Frontend do sistema Chat Edu - Assistente educacional com IA.

## 🚀 Tecnologias

- React 18 + TypeScript
- Vite (build tool)
- React Router (navegação)
- TanStack Query (gerenciamento de estado)
- Shadcn/ui + Radix UI (componentes)
- Tailwind CSS (estilização)

## 📋 Pré-requisitos

- Node.js 18+ ou Bun
- Backend rodando em `http://localhost:8000`

## 🔧 Instalação

1. Clone o repositório e navegue até a pasta do frontend:
```bash
cd chat-edu-frontend
```

2. Instale as dependências:
```bash
npm install
# ou
bun install
```

3. Configure as variáveis de ambiente:
```bash
cp .env.example .env
```

Edite o arquivo `.env` se necessário:
```env
VITE_API_URL=http://localhost:8000
```

## 🏃 Executando

### Modo Desenvolvimento
```bash
npm run dev
# ou
bun dev
```

O frontend estará disponível em `http://localhost:8080`

### Build para Produção
```bash
npm run build
# ou
bun run build
```

### Preview da Build
```bash
npm run preview
# ou
bun preview
```

## 📁 Estrutura do Projeto

```
src/
├── components/
│   ├── auth/          # Componentes de autenticação
│   ├── chat/          # Componentes do chat
│   ├── flashcards/    # Componentes de flashcards
│   ├── layout/        # Header, Sidebar
│   └── ui/            # Componentes UI (Shadcn)
├── contexts/
│   ├── AuthContext.tsx    # Gerenciamento de autenticação
│   └── CourseContext.tsx  # Gerenciamento de curso selecionado
├── pages/
│   ├── Login.tsx      # Página de login
│   ├── Dashboard.tsx  # Página principal
│   └── NotFound.tsx   # Página 404
├── services/
│   └── api.ts         # Chamadas à API
└── types/
    └── index.ts       # Tipos TypeScript
```

## 🔌 Integração com Backend

O frontend se comunica com os seguintes endpoints:

- `POST /login/` - Autenticação
- `POST /chat` - Envio de mensagens
- `POST /flashcards/{courseId}` - Geração de flashcards
- `POST /mindmaps/{courseId}` - Geração de mapas mentais
- `POST /retriever/{courseId}` - Busca de embeddings

## ✨ Funcionalidades

- ✅ Autenticação com persistência de sessão
- ✅ Chat com IA por curso
- ✅ Geração de flashcards
- ✅ Exibição de fontes das respostas
- ✅ Seleção de cursos
- ✅ Tema claro/escuro
- 🚧 Mapas mentais (em desenvolvimento)

## 🐛 Troubleshooting

### Erro de conexão com API
Verifique se:
1. O backend está rodando em `http://localhost:8000`
2. A variável `VITE_API_URL` está configurada corretamente
3. Não há problemas de CORS

### Sessão não persiste
Limpe o localStorage do navegador:
```javascript
localStorage.clear()
```

## 📝 Licença

Este projeto é parte do sistema Chat Edu.

---

## Lovable Project Info

**URL**: https://lovable.dev/projects/8aed65ab-6b0d-465f-973c-3f70afb16621

Changes made via Lovable will be committed automatically to this repo.
