# Sistema de Alimentador Automático com ESP32 e Flask

Este projeto é uma solução completa para gerenciar alimentadores automáticos de pets usando ESP32 e uma interface web moderna.

## 🚀 Funcionalidades

- **Dashboard Web**: Controle centralizado de todos os alimentadores.
- **API REST**: Comunicação eficiente e segura com os dispositivos ESP32.
- **Logs Detalhados**: Histórico de todas as alimentações (automáticas ou manuais).
- **Comandos em Tempo Real**: Envie comandos "Alimentar Agora" remotamente.
- **Segurança**: Autenticação via Token Bearer para cada dispositivo.

## 📂 Estrutura do Projeto

```
/app
    /routes         # Rotas da API e Dashboard
    /models         # Modelos do Banco de Dados (SQLAlchemy)
    /services       # Lógica de negócios (Auth, Comandos)
    /templates      # Páginas HTML (Jinja2 + Bootstrap)
config.py           # Configurações do Flask
database.py         # Instância do DB
main.py             # Ponto de entrada da aplicação
esp32_feeder.ino    # Firmware para o ESP32
```

## 🛠️ Como Rodar

### 1. Pré-requisitos
- Python 3.8+
- Pip

### 2. Instalação
```bash
pip install -r requirements.txt
```

### 3. Executar o Servidor
```bash
python main.py
```
O servidor iniciará em `http://localhost:5000`. O banco de dados `feeders.db` será criado automaticamente na primeira execução.

## 🤖 Configurando o ESP32

1. Abra o arquivo `esp32_feeder.ino` na Arduino IDE.
2. Instale as bibliotecas necessárias: `ArduinoJson`, `ESP32Servo`.
3. Registre um novo feeder via API (pode usar Postman ou Curl):
   ```bash
   POST http://localhost:5000/api/feeder/register
   Body: { "name": "Feeder Sala" }
   ```
   A resposta conterá o `id` e o `token`.
4. Atualize as variáveis no código do ESP32:
   - `ssid` e `password` do seu WiFi.
   - `serverUrl` com o IP do seu computador (ex: `http://192.168.0.10:5000/api`).
   - `feederToken` e `feederId` com os dados recebidos no registro.
5. Faça o upload para o ESP32.

## 📚 API Endpoints

- `POST /api/feeder/register`: Registra novo dispositivo.
- `GET /api/feeder/<id>/config`: Obtém configurações (intervalo, duração).
- `POST /api/feeder/<id>/status`: Reporta status e saúde.
- `GET /api/feeder/<id>/command`: Busca comandos pendentes.
- `POST /api/feeder/<id>/ack`: Confirma execução de comando.

## 🖥️ Dashboard

Acesse `http://localhost:5000` para ver seus dispositivos, editar configurações e visualizar logs.
