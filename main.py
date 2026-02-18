import pyaudio
import wave
import whisper
import google.generativeai as genai
import os
from dotenv import load_dotenv # Importe novo
import time

load_dotenv()
# --- CONFIGURAÇÕES DO DENNYS ---
# Pega a chave de forma segura
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# 2. Configurações de Áudio (Baseadas no seu teste)
DEVICE_INDEX = 1        # VB-Cable
SAMPLE_RATE = 48000     # Frequência correta
CHUNK = 1024
CHANNELS = 2
DURACAO_GRAVACAO = 60   # Gravando 1 minuto para teste
ARQUIVO_AUDIO = "aula_temp.wav"
MODELO_WHISPER = "base" # Modelo rápido

def gravar_audio():
    p = pyaudio.PyAudio()
    
    print(f"\n🔴 INICIANDO GRAVAÇÃO ({DURACAO_GRAVACAO}s)...")
    print("👉 Dê o PLAY no vídeo/aula agora!")
    
    try:
        stream = p.open(format=pyaudio.paInt16,
                        channels=CHANNELS,
                        rate=SAMPLE_RATE,
                        input=True,
                        input_device_index=DEVICE_INDEX,
                        frames_per_buffer=CHUNK)
        
        frames = []
        
        # Barra de progresso visual
        print("   Gravando", end="")
        for i in range(0, int(SAMPLE_RATE / CHUNK * DURACAO_GRAVACAO)):
            data = stream.read(CHUNK)
            frames.append(data)
            if i % 40 == 0: 
                print(".", end="", flush=True) # Pontinhos para mostrar que está vivo
        
        print("\n⏹️ Gravação finalizada.")
        
        stream.stop_stream()
        stream.close()
        p.terminate()

        wf = wave.open(ARQUIVO_AUDIO, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        return True
        
    except Exception as e:
        print(f"\n❌ Erro na gravação: {e}")
        return False

def transcrever_e_resumir():
    if not os.path.exists(ARQUIVO_AUDIO):
        print("Arquivo de áudio não encontrado.")
        return

    # --- PARTE 1: WHISPER (Ouvido -> Texto) ---
    print("\n📝 Transcrevendo áudio (pode levar uns 30s-1min)...")
    try:
        # Carrega o modelo (na primeira vez ele baixa 140MB, demora um pouquinho)
        model = whisper.load_model(MODELO_WHISPER)
        
        # Transcreve (fp16=False evita erros em PCs sem placa de vídeo NVIDIA)
        result = model.transcribe(ARQUIVO_AUDIO, fp16=False) 
        texto_transcrito = result["text"]
        
        print(f"\n--- Texto Detectado ---\n{texto_transcrito[:300]}...\n(texto completo enviado para IA)\n")
    except Exception as e:
        print(f"❌ Erro no Whisper: {e}")
        return

    # --- PARTE 2: GEMINI (Texto -> Resumo Inteligente) ---
    print("🧠 A IA está lendo e resumindo...")
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-3-flash-preview')
        
        prompt = f"""
        Aja como um Engenheiro de Software Sênior ajudando um estudante.
        Analise a transcrição abaixo (que pode conter erros de áudio).
        
        1. Dê um Título Profissional para o assunto.
        2. Faça um Resumo em Tópicos (Bullet Points).
        3. Destaque em negrito termos técnicos, ferramentas ou códigos mencionados.
        4. Se houver tarefas/prazos, liste separadamente.
        
        Transcrição:
        {texto_transcrito}
        """
        
        response = model.generate_content(prompt)
        resumo = response.text
        
        # Salva o resultado
     # --- INTEGRAÇÃO OBSIDIAN ---
        # Configure aqui o caminho da pasta onde você guarda suas notas
        # Dica: Use barras duplas \\ no Windows ou r"C:\..."
        CAMINHO_OBSIDIAN = r"C:\Users\Dennys Alves\OneDrive\Documentos\Dennys\Obsidian" 
        
        # Garante que a pasta existe
        os.makedirs(CAMINHO_OBSIDIAN, exist_ok=True)
        
        titulo_arquivo = f"Resumo_Aula_{int(time.time())}.md"
        caminho_completo = os.path.join(CAMINHO_OBSIDIAN, titulo_arquivo)
        
        with open(caminho_completo, "w", encoding="utf-8") as f:
            f.write(resumo)
        
        print("\n" + "="*40)
        print(f"✅ SUCESSO! Salvo no Obsidian: {titulo_arquivo}")
        print("="*40)
        print(resumo)

    except Exception as e:
        print(f"❌ Erro na API do Gemini: {e}")

if __name__ == "__main__":
    if gravar_audio():
        transcrever_e_resumir()