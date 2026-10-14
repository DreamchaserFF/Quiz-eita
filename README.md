# Quiz-eita

API para criação e aplicação de quizzes usando inteligência artificial. O projeto foi criado para o encontro de tecnologia da Faculdade Anhanguera e gera perguntas a partir de um tema, uma quantidade e um nível de dificuldade informados pelo cliente.

## Objetivo

O Quiz-eita recebe os parâmetros de um quiz, solicita ao Google Gemini perguntas em formato estruturado e disponibiliza o resultado por uma API HTTP. A geração acontece em segundo plano: a rota de criação responde rapidamente com um identificador, enquanto o processamento continua de forma assíncrona. O resultado e o estado do processamento ficam armazenados no Redis.

O projeto oferece recursos para:

- criar um quiz com tema, quantidade e dificuldade;
- consultar as perguntas depois que a geração terminar;
- enviar uma resposta e receber a alternativa correta, o indicador de acerto e a explicação;
- excluir um ou vários quizzes do Redis;
- verificar se a API está disponível por meio de um health check.

Os temas possuem prompts específicos para Python, Java, JavaScript, C#, filmes, jogos, músicas e pessoas famosas. Qualquer outro tema também pode ser enviado; nesse caso, é usado somente o prompt geral.

## Como o processamento funciona

1. `POST /quiz/create` gera um UUID e grava `quiz:<uuid>` no Redis com status `processing`.
2. Uma tarefa em segundo plano executa o grafo LangGraph e chama o Gemini com saída estruturada no modelo `Quiz`.
3. Quando a geração termina, o Redis recebe o quiz e o status `completed`. Em caso de erro, o status passa para `failed` e o erro é armazenado.
4. `POST /quiz/question` e `POST /quiz/answer` só retornam dados quando o status é `completed`. Enquanto o quiz está sendo gerado, a resposta é `null`.

## Arquitetura do projeto

```text
quiz-eita/
├── .env                         # chaves do Gemini e URLs (não versionar)
├── eita-rag-b1b0272909ff.json   # credencial local do Google Drive (não versionar)
├── quiz/
│   └── src/
│       ├── app/
│       │   ├── graph/               # grafo LangGraph e nós de geração
│       │   └── prompts/             # prompt geral e prompts por tema
│       ├── domain/
│       │   └── entities/quiz.py     # modelos Pergunta e Quiz (Pydantic)
│       ├── infra/
│       │   ├── llm/                 # cliente Gemini e rotação de chaves
│       │   └── repository/           # cliente e repositório Redis
│       ├── presentation/
│       │   ├── http/                # aplicação FastAPI, rotas, schemas e serviços
│       │   └── cli/                 # espaço reservado para a interface CLI
│       └── main.py                  # código de teste do repositório Redis
├── requirements.txt                 # dependências Python fixadas
├── start.ps1                        # atalho legado para iniciar o servidor
├── venv/                            # ambiente virtual local (criado pelo desenvolvedor)
└── README.md
```

A aplicação ASGI está em `quiz/src/presentation/http/main.py`. O módulo expõe o objeto `app` e registra as rotas de `presentation.http.routes.quiz`.

## Pré-requisitos

- Windows com PowerShell (os comandos abaixo também podem ser adaptados para Linux/macOS);
- Python 3.11 ou superior. O ambiente usado no desenvolvimento deste repositório é Python 3.11.0;
- pip atualizado;
- um servidor Redis acessível pela aplicação;
- uma ou mais chaves de API do Google Gemini.

Confira a versão instalada antes de começar:

```powershell
py --version
python --version
```

## Criar a `venv`

A `venv` deve ficar na raiz do projeto, no mesmo nível de `requirements.txt` e da pasta `quiz`:

```text
C:\cod\Quiz-eita\venv
```

A partir da raiz do repositório, crie o ambiente com o Python 3.11:

```powershell
cd C:\cod\Quiz-eita
py -3.11 -m venv .\venv
```

Ative-o no PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

Se a política de execução do PowerShell bloquear a ativação, libere somente a sessão atual e tente novamente:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

É possível usar a `venv` sem ativá-la, chamando diretamente `venv\Scripts\python.exe`. Essa forma é usada nos comandos de execução abaixo e evita depender do estado do terminal.

## Instalar todas as dependências

Com a `venv` ativa (ou usando o executável dela diretamente), atualize o pip e instale o arquivo de dependências:

```powershell
cd C:\cod\Quiz-eita
python -m pip install --upgrade pip
python -m pip install -r .\requirements.txt
```

Sem ativar o ambiente virtual:

```powershell
.\venv\Scripts\python.exe -m pip install --upgrade pip
.\venv\Scripts\python.exe -m pip install -r .\requirements.txt
```

As dependências principais são:

- **FastAPI** e **Uvicorn**: API HTTP e servidor ASGI;
- **Pydantic**: validação dos requests e das perguntas geradas;
- **LangGraph** e **LangChain**: orquestração do fluxo de geração;
- **langchain-google-genai**: integração com o Gemini;
- **python-dotenv**: carregamento das variáveis do arquivo `.env`;
- **redis**: cliente assíncrono para persistência dos quizzes;
- **pytest**: suporte a testes automatizados.

Para confirmar a instalação básica:

```powershell
.\venv\Scripts\python.exe -c "import fastapi, uvicorn, redis, langgraph, langchain_google_genai; print('Dependências carregadas com sucesso')"
```

## Configurar variáveis de ambiente

Crie ou edite o arquivo:

```text
C:\cod\Quiz-eita\.env
```

Use o seguinte formato e substitua os valores pelas suas credenciais:

```dotenv
REDIS_URL=redis://localhost:6379/0
EITA_1=sua-chave-do-gemini-1
EITA_2=sua-chave-do-gemini-2
```

O código lê `REDIS_URL` e as chaves `EITA_1`, `EITA_2`, `EITA_4`, `EITA_5`, `EITA_6`, `EITA_7`, `EITA_8`, `EITA_9` e `EITA_10`. Basta cadastrar uma chave para executar o projeto; as demais são opcionais e permitem alternância quando o Gemini responde com limite `429`. A variável `EITA_3` não é usada pelo gerenciador de chaves atual.

Não compartilhe nem faça commit desse arquivo. O `.gitignore` já ignora arquivos `.env`.

## Iniciar o Redis

O pacote Python `redis` é apenas o cliente; é necessário executar um servidor Redis. Com o Docker Desktop instalado, uma forma simples de iniciar uma instância local é:

```powershell
docker run --name quiz-eita-redis -p 6379:6379 -d redis:7-alpine
```

Se o container já existir e estiver parado, inicie-o com:

```powershell
docker start quiz-eita-redis
```

O valor `REDIS_URL=redis://localhost:6379/0` usa o banco lógico `0`. Também é possível apontar `REDIS_URL` para uma instância gerenciada ou para outro host, desde que a URL seja compatível com o cliente Redis assíncrono.

## Rodar o FastAPI

Execute os comandos a partir da raiz `C:\cod\Quiz-eita`, depois de configurar `.env` e iniciar o Redis:

```powershell
.\venv\Scripts\python.exe -m uvicorn presentation.http.main:app --app-dir .\quiz\src --reload
```

O servidor ficará disponível em `http://127.0.0.1:8000`. A opção `--app-dir .\quiz\src` é necessária porque o pacote `presentation` está dentro de `quiz/src`.

Para escolher host e porta explicitamente:

```powershell
.\venv\Scripts\python.exe -m uvicorn presentation.http.main:app `
  --app-dir .\quiz\src `
  --host 127.0.0.1 `
  --port 8000 `
  --reload
```

O arquivo `start.ps1` é um atalho legado e pressupõe execução a partir de `quiz`. Para evitar ambiguidade de diretório e garantir o interpretador da `venv`, use o comando acima a partir da raiz.

### Verificar a API

Em outro terminal:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Resposta esperada:

```json
{"status":"ok"}
```

Documentação interativa gerada pelo FastAPI:

- Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- OpenAPI: [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)

## API HTTP

### `GET /health`

Verifica se o processo FastAPI está ativo.

```json
{"status":"ok"}
```

### `POST /quiz/create`

Inicia a geração de um quiz e retorna o UUID imediatamente.

Request:

```json
{
  "tema": "python",
  "quantidade": 5,
  "dificuldade": "mista"
}
```

Exemplo PowerShell:

```powershell
$body = @{
  tema = "python"
  quantidade = 5
  dificuldade = "mista"
} | ConvertTo-Json

$criado = Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/quiz/create `
  -ContentType "application/json" `
  -Body $body

$criado
```

Resposta:

```json
{"uuid":"código-gerado"}
```

`tema` e `dificuldade` precisam ser textos não vazios. `quantidade` deve ser maior que zero. Requests inválidos retornam `422`.

### `POST /quiz/question`

Consulta as perguntas de um quiz concluído:

```json
{
  "uuid": "código-gerado"
}
```

Quando o quiz está pronto:

```json
{
  "perguntas": [
    {
      "enunciado": "Qual estrutura é usada para criar uma lista em Python?",
      "alternativas": ["[]", "{}", "()", "<>"]
    }
  ]
}
```

Durante `processing`, ou quando o quiz está em `failed`, a rota retorna `null`. As alternativas são embaralhadas antes da resposta, portanto a ordem pode mudar entre consultas.

### `POST /quiz/answer`

Corrige uma resposta pelo texto exato do enunciado:

```json
{
  "uuid": "código-gerado",
  "enunciado": "Qual estrutura é usada para criar uma lista em Python?",
  "resposta_usuario": "[]"
}
```

Resposta quando o enunciado é encontrado:

```json
{
  "resposta": {
    "resposta": "[]",
    "correta": true,
    "explicacao": "Colchetes criam listas em Python."
  }
}
```

Assim como em `/quiz/question`, a resposta é `null` enquanto o quiz não estiver concluído. Se o enunciado não existir no quiz, a rota também não encontra uma resposta.

### `DELETE /quiz/delete`

Exclui um ou mais quizzes do Redis:

```json
{
  "list_uuid": [
    {"uuid": "código-gerado"},
    {"uuid": "outro-código"}
  ]
}
```

Resposta:

```json
{"excluded": true}
```

## Estados armazenados no Redis

Cada quiz usa a chave `quiz:<uuid>`:

- `processing`: UUID criado e geração em andamento;
- `completed`: perguntas geradas e salvas no campo `quiz`;
- `failed`: geração ou leitura falhou e o campo `error` contém a mensagem.

Para inspecionar chaves em desenvolvimento, prefira `SCAN` a `KEYS`:

```powershell
docker exec quiz-eita-redis redis-cli SCAN 0 MATCH "quiz:*" COUNT 100
```

## Testes e validações locais

Não há uma suíte de testes no repositório neste momento. É possível validar a importação da aplicação e a configuração da API com:

```powershell
.\venv\Scripts\python.exe -c "import sys; sys.path.insert(0, 'quiz/src'); from presentation.http.main import app; print(app.title)"
```

Com Redis, chaves do Gemini e o servidor FastAPI ativos, use `/health` e os exemplos das rotas acima para fazer um teste manual completo.

## Deploy com Docker e Dockploy

O `Dockerfile` da raiz usa duas etapas: compila o Vue com Node.js e depois copia o `dist` para uma imagem Python que executa o FastAPI. O FastAPI serve o front e a API no mesmo endereço, na porta `8000`. Não use `--reload` no container de produção.

### Testar a imagem localmente

Com o Docker Desktop em execução, a partir da raiz do repositório:

```powershell
docker build -t quiz-eita:local .
docker run --rm -p 8000:8000 `
  -e REDIS_URL="redis://host.docker.internal:6379/0" `
  -e REDIS_URL_RAG="redis://host.docker.internal:6379/0" `
  -e EITA_1="sua-chave-do-gemini" `
  quiz-eita:local
```

Abra `http://localhost:8000/` para o front e `http://localhost:8000/health` para o health check. Em uma VPS, substitua `host.docker.internal` pelo endereço ou nome do serviço Redis acessível pelo container.

### Valores do recurso no Dockploy

Na origem GitHub, selecione o repositório `Quiz-eita`, a branch `main`, o caminho de build `/` e o gatilho `On Push`. Na seção de build, use:

| Campo | Valor |
|---|---|
| Build Type | `Dockerfile` |
| Docker File | `Dockerfile` |
| Docker Context Path | `.` (ou `/`, conforme a representação do Dockploy) |
| Docker Build Stage | `production` |
| Porta publicada | `8000` |

O estágio `production` é o estágio final do Dockerfile. O watch path pode incluir `Dockerfile`, `requirements.txt`, `quiz/**`, `interface-quiz/**` e `.dockerignore`. Assim, um push na `main` que altere qualquer parte da aplicação dispara um novo build.

### Variáveis e segredos

Cadastre no ambiente do Dockploy, sem versionar valores no Git:

```dotenv
REDIS_URL=redis://usuario:senha@host:6379/0
REDIS_URL_RAG=redis://usuario:senha@host:6379/0
EITA_1=sua-chave-do-gemini-1
EITA_2=sua-chave-do-gemini-2
GOOGLE_DRIVE_FOLDER_ID=id-da-pasta
GOOGLE_DRIVE_CREDENTIALS_NAME=/run/secrets/google-drive.json
# somente se o front estiver em outro domínio
CORS_ORIGINS=https://app.exemplo.com
```

`REDIS_URL` guarda os quizzes e `REDIS_URL_RAG` é usado pelo contexto de documentos; eles podem apontar para a mesma instância Redis, mas os dois nomes precisam existir no ambiente atual. Para a sincronização do Google Drive, monte a credencial JSON como um secret no caminho informado por `GOOGLE_DRIVE_CREDENTIALS_NAME`. O arquivo não deve ser copiado para a imagem nem enviado ao repositório.

Se o Dockploy oferecer um domínio separado para a API, defina `VITE_API_URL` **antes do build** com a URL pública da API, por exemplo `https://api.exemplo.com`, e inclua o domínio do front em `CORS_ORIGINS`. Para o desenho de um único container, deixe `VITE_API_URL` vazia: o front usará a mesma origem automaticamente.

Depois do primeiro deploy, valide `https://seu-dominio/health` e `https://seu-dominio/`. O endpoint de health confirma que o processo está ativo; a criação de quiz também depende de Redis, das chaves Gemini e, quando houver contexto documental, do Google Drive.

## Solução de problemas

### `REDIS_URL não foi configurada`

Confirme que `.env` existe na raiz do repositório, contém uma linha `REDIS_URL=...` não vazia e que o processo foi iniciado com o comando da raiz do projeto. Verifique também se o Redis está em execução e acessível no host e na porta informados.

### Erro de importação de `presentation` ou `domain`

O servidor deve ser iniciado com `--app-dir .\quiz\src` quando o comando é executado em `C:\cod\Quiz-eita`. Iniciar Uvicorn sem esse diretório faz o Python procurar os pacotes no local errado.

### O quiz permanece em `processing`

Confira os logs do Uvicorn, a conectividade com o Redis e a existência de ao menos uma chave `EITA_*` válida. Falhas do Gemini mudam o estado para `failed`; nesse caso, consulte o log do servidor para identificar a causa.

### Limite de requisições do Gemini (`429`)

O `GeminiKeyManager` alterna entre as chaves configuradas. Cadastre mais chaves válidas em `.env` se a aplicação atingir o limite de uma chave.

## Segurança e operação

- mantenha `.env` e `eita-rag-b1b0272909ff.json` fora do controle de versão;
- não registre nem compartilhe valores de `REDIS_URL` ou das chaves do Gemini;
- em produção, use Redis com autenticação, TLS e regras de rede adequadas;
- `--reload` é útil durante o desenvolvimento, mas deve ser desligado em produção;
- configure um processo supervisor ou um servidor de contêiner para manter o Uvicorn ativo.
