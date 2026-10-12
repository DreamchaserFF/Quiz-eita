export interface Pergunta {
    enunciado: string
    alternativas: string[]
} //como a api enxerga uma pergunta
    
export interface Resposta {
    enunciado: string
    resposta: string
}

export interface CriarQuizRequest {
    tema: string
    quantidade: number
    dificuldade: string
} //interace para criar um quiz

export interface BuscarQuizResponse {
    perguntas: Pergunta[]
} //interface para receber um quiz

export interface RespostaRequest{
    uuid: string
    respostas: Resposta[]
}