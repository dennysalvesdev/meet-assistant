import pyaudio
import wave

# Configurações Iniciais
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2  # Se der erro, o script tenta mudar para 1 automaticamente
SECONDS = 5   # Gravação rápida de teste
OUTPUT_FILENAME = "teste_final.wav"

p = pyaudio.PyAudio()

print("\n🔍 PROCURANDO PELO CABO VIRTUAL E TESTANDO CONFIGURAÇÕES...\n")

# Lista de palavras-chave para achar o cabo
keywords = ["CABLE Output", "VB-Audio"]
candidatos = []

# 1. Achar todos os possíveis índices do Cabo
for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    nome = info['name']
    if any(k in nome for k in keywords):
        candidatos.append((i, nome))

if not candidatos:
    print("❌ ERRO: Não achei nenhum dispositivo com nome 'CABLE Output'.")
    print("Verifique se o VB-Cable está instalado.")
    exit()

# 2. Testar cada candidato com diferentes frequências
sucesso = False
stream = None
index_escolhido = None
rate_escolhido = None

frequencias_teste = [48000, 44100, 96000] # As mais comuns

for index, nome in candidatos:
    print(f"👉 Testando Device {index}: {nome}")
    
    for taxa in frequencias_teste:
        try:
            # Tenta abrir o stream
            stream = p.open(format=FORMAT,
                            channels=CHANNELS,
                            rate=taxa,
                            input=True,
                            input_device_index=index,
                            frames_per_buffer=CHUNK)
            
            # Se chegou aqui, funcionou!
            print(f"   ✅ SUCESSO! Conectado em {taxa}Hz no Index {index}.")
            sucesso = True
            index_escolhido = index
            rate_escolhido = taxa
            break # Sai do loop de taxas
        except Exception as e:
            print(f"   ❌ {taxa}Hz falhou.")
            if stream:
                stream.close()
    
    if sucesso:
        break # Sai do loop de dispositivos

if not sucesso:
    print("\n❌ FALHA TOTAL: Nenhum dispositivo aceitou a conexão.")
    print("DICA: Vá em Painel de Controle de Som -> Gravação -> CABLE Output -> Propriedades -> Avançado e veja a taxa de Hz (ex: 2 canais, 24 bits, 48000Hz).")
    p.terminate()
    exit()

# 3. Gravar de verdade
print(f"\n🔴 GRAVANDO AGORA (Device {index_escolhido} @ {rate_escolhido}Hz)...")
print("🔊 Dê play em algum vídeo/música para testar!")

frames = []
for i in range(0, int(rate_escolhido / CHUNK * SECONDS)):
    try:
        data = stream.read(CHUNK)
        frames.append(data)
    except Exception as e:
        print(f"Erro durante gravação: {e}")
        break

print("⏹️ Gravação finalizada.")

stream.stop_stream()
stream.close()
p.terminate()

# Salvar
wf = wave.open(OUTPUT_FILENAME, 'wb')
wf.setnchannels(CHANNELS)
wf.setsampwidth(p.get_sample_size(FORMAT))
wf.setframerate(rate_escolhido)
wf.writeframes(b''.join(frames))
wf.close()

print(f"💾 Arquivo salvo: {OUTPUT_FILENAME}")
print("🎧 Abra o arquivo e veja se ouve o som do sistema.")