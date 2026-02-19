import customtkinter as ctk
import threading
import pyaudio
import wave
import os
import time
import re
import whisper
import google.generativeai as genai
from datetime import datetime
from dotenv import load_dotenv

# --- CONFIGURAÇÕES GLOBAIS ---
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

DEVICE_INDEX = 1
SAMPLE_RATE = 48000
CHUNK = 1024
CHANNELS = 2

# Configuração de Tema
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

class MeetAssistantApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- JANELA PRINCIPAL ---
        self.title("Meet Assistant AI")
        self.geometry("320x340") # Aumentei altura para caber o novo botão
        self.resizable(False, False)
        self.attributes("-topmost", True)
        
        # Variáveis de Estado
        self.gravando = False
        self.pausado = False  # Nova flag de controle
        self.frames = []
        self.inicio_gravacao = None
        self.tempo_pausado = 0 # Para descontar o tempo de pausa do timer

        # --- UI LAYOUT ---
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=15)

        # 1. Inputs
        self.label_inputs = ctk.CTkLabel(self.main_frame, text="Configuração da Nota", font=("Roboto", 12, "bold"))
        self.label_inputs.pack(anchor="w")

        self.entry_materia = ctk.CTkEntry(self.main_frame, placeholder_text="Matéria (ex: Java)")
        self.entry_materia.pack(fill="x", pady=(0, 5))

        self.entry_tema = ctk.CTkEntry(self.main_frame, placeholder_text="Tema da Aula (ex: Arrays)")
        self.entry_tema.pack(fill="x", pady=(0, 15))

        # 2. Cronômetro
        self.label_timer = ctk.CTkLabel(
            self.main_frame, 
            text="00:00", 
            font=("Roboto", 35, "bold"),
            text_color="white"
        )
        self.label_timer.pack(pady=(0, 5))
        
        # Label de Status (ex: "EM PAUSA")
        self.label_substatus = ctk.CTkLabel(self.main_frame, text="", font=("Roboto", 12, "bold"), text_color="yellow")
        self.label_substatus.pack(pady=(0, 10))

        # 3. Botões de Controle
        # Botão Principal (Gravar/Parar)
        self.btn_acao = ctk.CTkButton(
            self.main_frame, 
            text="INICIAR GRAVAÇÃO",
            font=("Roboto", 12, "bold"),
            height=40,
            fg_color="#6C63FF",
            hover_color="#5a52d5",
            command=self.toggle_gravacao
        )
        self.btn_acao.pack(fill="x")

        # Botão de Pausa (Inicialmente escondido ou desativado)
        self.btn_pausa = ctk.CTkButton(
            self.main_frame, 
            text="⏸ PAUSAR",
            font=("Roboto", 12, "bold"),
            height=30,
            fg_color="#FFA502",
            hover_color="#e58e00",
            state="disabled", # Começa desativado
            command=self.toggle_pausa
        )
        self.btn_pausa.pack(fill="x", pady=(10, 0))

    def toggle_gravacao(self):
        if not self.gravando:
            self.iniciar_servico()
        else:
            self.parar_servico()

    def toggle_pausa(self):
        # Inverte o estado (Se tá pausado, despausa. Se tá gravando, pausa)
        self.pausado = not self.pausado
        
        if self.pausado:
            self.btn_pausa.configure(text="▶ RETOMAR", fg_color="#2ED573", hover_color="#26af61")
            self.label_substatus.configure(text="⏸ EM PAUSA")
            # Registra quando a pausa começou para descontar do timer depois
            self.inicio_pausa_atual = datetime.now()
        else:
            self.btn_pausa.configure(text="⏸ PAUSAR", fg_color="#FFA502", hover_color="#e58e00")
            self.label_substatus.configure(text="")
            # Calcula quanto tempo ficou parado e adiciona ao acumulador
            delta_pausa = datetime.now() - self.inicio_pausa_atual
            self.tempo_pausado += delta_pausa.total_seconds()

    def atualizar_cronometro(self):
        if self.gravando:
            if not self.pausado:
                agora = datetime.now()
                # Tempo total decorrido MENOS o tempo que ficou pausado
                delta_total = (agora - self.inicio_gravacao).total_seconds() - self.tempo_pausado
                
                mins, segs = divmod(int(delta_total), 60)
                self.label_timer.configure(text=f"{mins:02}:{segs:02}")
            
            self.after(1000, self.atualizar_cronometro)

    def iniciar_servico(self):
        self.gravando = True
        self.pausado = False
        self.frames = []
        self.inicio_gravacao = datetime.now()
        self.tempo_pausado = 0
        
        # Trava inputs
        self.entry_materia.configure(state="disabled")
        self.entry_tema.configure(state="disabled")
        
        # Atualiza botões
        self.btn_acao.configure(text="⏹ PARAR E SALVAR", fg_color="#FF4757", hover_color="#e04050")
        self.btn_pausa.configure(state="normal", text="⏸ PAUSAR", fg_color="#FFA502")
        self.label_substatus.configure(text="")
        
        self.atualizar_cronometro()
        threading.Thread(target=self.gravar_audio_loop).start()

    def gravar_audio_loop(self):
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=CHANNELS, rate=SAMPLE_RATE,
                        input=True, input_device_index=DEVICE_INDEX, frames_per_buffer=CHUNK)
        
        while self.gravando:
            if self.pausado:
                # Se estiver pausado, apenas dorme um pouco para não gastar CPU
                time.sleep(0.1) 
                continue

            try:
                # Lê o áudio e salva
                data = stream.read(CHUNK)
                self.frames.append(data)
            except Exception as e:
                # Evita crash se o buffer encher
                print(f"Frame drop: {e}")
                
        stream.stop_stream()
        stream.close()
        p.terminate()

    def parar_servico(self):
        self.gravando = False
        self.pausado = False
        
        self.label_substatus.configure(text="PROCESSANDO IA...", text_color="#00d2d3")
        self.btn_acao.configure(state="disabled", text="AGUARDE...")
        self.btn_pausa.configure(state="disabled")
        
        # Captura nomes
        materia_raw = self.entry_materia.get().strip() or "Geral"
        tema_raw = self.entry_tema.get().strip()
        
        # Salva wav
        nome_wav = "temp_audio.wav"
        with wave.open(nome_wav, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(b''.join(self.frames))
        
        threading.Thread(target=self.processar_final, args=(nome_wav, materia_raw, tema_raw)).start()

    def processar_final(self, arquivo, materia, tema):
        try:
            # 1. Transcrição (Whisper)
            model_w = whisper.load_model("base")
            result = model_w.transcribe(arquivo, fp16=False)
            texto_transcrito = result['text'].strip()

            # --- TRAVA DE SEGURANÇA 1: Áudio Vazio ou Muito Curto ---
            if len(texto_transcrito) < 50:
                print("Áudio muito curto ou vazio. Resumo cancelado.")
                self.label_substatus.configure(text="⚠️ Áudio Vazio/Curto", text_color="orange")
                # Encerra sem gastar API do Gemini
                self.btn_acao.configure(state="normal", text="NOVA GRAVAÇÃO", fg_color="#6C63FF")
                self.entry_materia.configure(state="normal")
                self.entry_tema.configure(state="normal")
                return

            # --- TRAVA DE SEGURANÇA 2: Prompt Blindado ---
            model_ai = genai.GenerativeModel('gemini-3-flash-preview')
            
            prompt = f"""
            Você é um assistente de anotações acadêmicas experiente.
            
            Contexto da Matéria: {materia}
            
            Instrução: 
            Faça um resumo técnico detalhado em Markdown baseando-se EXCLUSIVAMENTE no texto transcrito abaixo.
            Se o texto for desconexo, apenas ruído ou não tiver conteúdo relevante, responda apenas: "Não foi possível identificar conteúdo relevante nesta gravação."
            
            Texto Transcrito:
            "{texto_transcrito}"
            """
            
            response = model_ai.generate_content(prompt)
            
            # Limpeza de nomes e criação de pastas
            def limpar_nome(texto):
                return re.sub(r'[\\/*?:"<>|]', "", texto)

            materia_limpa = limpar_nome(materia) if materia else "Geral"
            
            if tema:
                nome_arquivo = f"{limpar_nome(tema)}.md"
            else:
                nome_arquivo = f"Resumo_{int(time.time())}.md"

            base_path = r"C:\Users\Dennys Alves\OneDrive\Documentos\Dennys\Obsidian"
            full_path = os.path.join(base_path, materia_limpa)
            os.makedirs(full_path, exist_ok=True)
            
            with open(os.path.join(full_path, nome_arquivo), "w", encoding="utf-8") as f:
                f.write(response.text)
            
            self.label_substatus.configure(text="✅ SALVO!", text_color="#2ED573")
            
        except Exception as e:
            self.label_substatus.configure(text="❌ ERRO", text_color="red")
            print(f"Erro no processamento: {e}")
        
        # Reseta UI (Sempre executado no final, mesmo com sucesso)
        self.btn_acao.configure(state="normal", text="NOVA GRAVAÇÃO", fg_color="#6C63FF")
        self.entry_materia.configure(state="normal")
        self.entry_tema.configure(state="normal")

if __name__ == "__main__":
    app = MeetAssistantApp()
    app.mainloop()