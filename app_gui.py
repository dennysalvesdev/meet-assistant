import customtkinter as ctk
import threading
import pyaudio
import wave
import os
import time
import whisper
import google.generativeai as genai
from datetime import datetime, timedelta
from dotenv import load_dotenv

# --- CONFIGURAÇÕES GLOBAIS ---
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

DEVICE_INDEX = 1
SAMPLE_RATE = 48000
CHUNK = 1024
CHANNELS = 2

# Configuração de Tema do CustomTkinter
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

class MeetAssistantApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- JANELA PRINCIPAL ---
        self.title("Meet Assistant AI")
        self.geometry("300x180")
        self.resizable(False, False)
        self.attributes("-topmost", True) # Sempre no topo
        
        # Variáveis de Estado
        self.gravando = False
        self.frames = []
        self.inicio_gravacao = None

        # --- LAYOUT (DESIGN) ---
        # Frame principal para dar um padding bonito
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # 1. Título / Status
        self.label_titulo = ctk.CTkLabel(
            self.main_frame, 
            text="Ready to Record", 
            font=("Roboto Medium", 16),
            text_color="#A0A0A0" # Cinza claro
        )
        self.label_titulo.pack(pady=(0, 5))

        # 2. Cronômetro (O destaque visual)
        self.label_timer = ctk.CTkLabel(
            self.main_frame, 
            text="00:00", 
            font=("Roboto", 40, "bold"),
            text_color="white"
        )
        self.label_timer.pack(pady=(0, 15))

        # 3. Botão de Ação
        self.btn_acao = ctk.CTkButton(
            self.main_frame, 
            text="INICIAR GRAVAÇÃO",
            font=("Roboto", 12, "bold"),
            height=40,
            fg_color="#6C63FF", # Roxo moderno (cor inicial)
            hover_color="#5a52d5",
            command=self.toggle_gravacao
        )
        self.btn_acao.pack(fill="x")

    def toggle_gravacao(self):
        if not self.gravando:
            self.iniciar_servico()
        else:
            self.parar_servico()

    def atualizar_cronometro(self):
        """Atualiza o texto 00:00 enquanto estiver gravando"""
        if self.gravando and self.inicio_gravacao:
            agora = datetime.now()
            delta = agora - self.inicio_gravacao
            # Formata para MM:SS
            segundos_totais = int(delta.total_seconds())
            minutos = segundos_totais // 60
            segundos = segundos_totais % 60
            tempo_formatado = f"{minutos:02}:{segundos:02}"
            
            self.label_timer.configure(text=tempo_formatado)
            
            # Chama essa mesma função daqui a 1000ms (1 segundo)
            self.after(1000, self.atualizar_cronometro)

    def iniciar_servico(self):
        self.gravando = True
        self.frames = []
        self.inicio_gravacao = datetime.now()
        
        # Muda Visual para "GRAVANDO"
        self.btn_acao.configure(text="PARAR E RESUMIR", fg_color="#FF4757", hover_color="#e04050") # Vermelho
        self.label_titulo.configure(text="● Gravando...", text_color="#FF4757")
        
        # Inicia o Cronômetro na tela
        self.atualizar_cronometro()

        # Thread de áudio
        self.thread_audio = threading.Thread(target=self.gravar_audio_loop)
        self.thread_audio.start()

    def gravar_audio_loop(self):
        p = pyaudio.PyAudio()
        try:
            stream = p.open(format=pyaudio.paInt16, channels=CHANNELS, rate=SAMPLE_RATE,
                            input=True, input_device_index=DEVICE_INDEX, frames_per_buffer=CHUNK)
            
            while self.gravando:
                data = stream.read(CHUNK)
                self.frames.append(data)
                
            stream.stop_stream()
            stream.close()
        except Exception as e:
            print(f"Erro no áudio: {e}")
        finally:
            p.terminate()

    def parar_servico(self):
        self.gravando = False
        self.inicio_gravacao = None
        
        # Feedback Visual de Processamento
        self.label_titulo.configure(text="Processando IA...", text_color="#FFA502") # Laranja
        self.label_timer.configure(text_color="#FFA502")
        self.btn_acao.configure(state="disabled", text="AGUARDE...", fg_color="#2F3542") # Cinza Escuro
        
        # Salva wav
        nome_wav = "aula_manual.wav"
        with wave.open(nome_wav, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(b''.join(self.frames))
        
        threading.Thread(target=self.processar_final, args=(nome_wav,)).start()

    def processar_final(self, arquivo):
        try:
            # Whisper
            model_w = whisper.load_model("base")
            result = model_w.transcribe(arquivo, fp16=False)
            
            # Gemini (Usando modelo estável)
            model_ai = genai.GenerativeModel('gemini-3-flash-preview')
            prompt = f"Aja como um Engenheiro Sênior. Resuma esta aula com precisão técnica: {result['text']}"
            response = model_ai.generate_content(prompt)
            
            # Obsidian
            caminho_obsidian = r"C:\Users\Dennys Alves\OneDrive\Documentos\Dennys\Obsidian"
            os.makedirs(caminho_obsidian, exist_ok=True)
            nome_nota = f"Resumo_Aula_{int(time.time())}.md"
            
            with open(os.path.join(caminho_obsidian, nome_nota), "w", encoding="utf-8") as f:
                f.write(response.text)
            
            # Sucesso na UI
            self.label_titulo.configure(text="Sucesso!", text_color="#2ED573") # Verde Neon
            self.label_timer.configure(text="SALVO", text_color="#2ED573")
            
        except Exception as e:
            self.label_titulo.configure(text="Erro", text_color="red")
            self.label_timer.configure(text="ERRO", font=("Roboto", 20))
            print(e)
        
        # Restaura botão
        self.btn_acao.configure(state="normal", text="NOVA GRAVAÇÃO", fg_color="#6C63FF", hover_color="#5a52d5")

if __name__ == "__main__":
    app = MeetAssistantApp()
    app.mainloop()