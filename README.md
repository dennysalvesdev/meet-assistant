# 🎙️ Meet-Assistant

O **Meet-Assistant** é uma ferramenta de produtividade desenvolvida para auxiliar estudantes e profissionais que precisam manter o foco total em aulas ou reuniões sem perder a qualidade das anotações. A ferramenta captura o áudio interno do sistema, transcreve o conteúdo e utiliza Inteligência Artificial para gerar resumos estruturados diretamente no **Obsidian**.

## 🚀 Funcionalidades

- **Captura de Áudio Interno**: Gravação de áudio do sistema (YouTube, Meet, Zoom) sem necessidade de microfone externo.
- **Transcrição de Alta Precisão**: Utiliza o modelo **Whisper (OpenAI)** para converter fala em texto de forma eficiente.
- **Resumo Inteligente**: Integração com a API do **Google Gemini** para estruturar títulos, tópicos principais e termos técnicos.
- **Integração com Obsidian**: Exportação automática dos resumos em formato Markdown para o seu cofre de notas.
- **Segurança**: Gerenciamento de chaves sensíveis via variáveis de ambiente (`.env`).

## 🛠️ Tecnologias Utilizadas

- **Linguagem**: Python 3.12+
- **IA/NLP**: OpenAI Whisper (Local) e Google Gemini API (Nuvem)
- **Processamento de Áudio**: PyAudio e Wave
- **Automação**: Python-dotenv
- **Ambiente**: VS Code e Git

## 📋 Pré-requisitos

Antes de rodar o projeto, você precisará de:
1. Um Cabo de Áudio Virtual (ex: **VB-CABLE**) configurado como saída e entrada padrão.
2. **FFmpeg** instalado no sistema (necessário para o processamento do Whisper).
3. Uma chave de API do **Google AI Studio**.

## 🔧 Configuração Inicial

1. Clone o repositório:
   ```bash
   git clone [Clique aqui para ver o projeto](https://github.com/dennysalvesdev/meet-assistant.git)
   ```

2. Crie e ative seu ambiente virtual:
    
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    ```
    
3. Instale as dependências:
    
    ```bash
    pip install pyaudio wave openai-whisper google-generativeai python-dotenv
    ```
    
4. Crie um arquivo `.env` na raiz e adicione sua chave:
    
    Snippet de código
    
    ```
    GEMINI_API_KEY=SUA_CHAVE_AQUI
    ```
    

## 📝 Como Usar

1. Execute o script principal:
    
    Bash
    
    ```
    python main.py
    ```
    
2. Dê o play no vídeo ou inicie sua reunião.
    
3. Ao final do tempo definido, o resumo será gerado e enviado automaticamente para a pasta configurada do seu **Obsidian**.
    

---

_Projeto desenvolvido por **Dennys Alves Silva** como parte dos estudos em Engenharia de Software na Jala University._   