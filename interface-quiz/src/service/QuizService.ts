import type { CriarQuizRequest, BuscarQuizResponse, RespostaRequest } from '../types/QuizTypes'

// Empty by default means same-origin in production. Set VITE_API_URL only
// when the API is intentionally hosted on another origin.
const API_URL = (import.meta.env.VITE_API_URL ?? '').replace(/\/$/, '')

//método de gerar quiz retornando um uuid em string
export async function criarQuiz(req: CriarQuizRequest): Promise<string> {

    const response = await fetch(`${API_URL}/quiz/create`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(req), 
    }) 

    if(!response.ok) throw new Error(`Erro ao criar quiz: ${response.status}`)
    
    const data = await response.json()
    if(!data?.uuid) throw new Error('Resposta sem uuid')
    return data.uuid
}

//método de procurar quiz usando uuid retornando BuscarQuizResponse ou null
export async function buscarQuiz(uuid: string): Promise<BuscarQuizResponse | null> {

    const response = await fetch(`${API_URL}/quiz/question`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({uuid}),
    })

    if(!response.ok) throw new Error(`Erro ao buscar perguntas: ${response.status}`)
    
    const data: BuscarQuizResponse| null = await response.json()
    return data?.perguntas && data.perguntas.length > 0 ? data : null
    //se data não for nulo, perguntas for um objeto válido e perguntas for maior que 0 
    // retorna data, se não null
}

//Método de enviar respostas usando uuid e uma lista de enunciados com alternatvias
export async function responderQuiz(request: RespostaRequest): Promise <number | null> {

    let acertos = 0
    const uuid = request.uuid

    for(let i=0; i<request.respostas.length; i++) {

        const enunciado = request.respostas[i].enunciado
        const resposta_usuario = request.respostas[i].resposta

        const response = await fetch(`${API_URL}/quiz/answer`, {

        method: 'POST',
        headers: { 'Content-Type' : 'application/json' },
        body: JSON.stringify({uuid, enunciado, resposta_usuario}),
    
        })

        if(!response.ok) throw new Error('Houve um erro ao registrar resposta')
        
        const data = await response.json()
        if(data.resposta.correta==true) {acertos++}
    }
    return acertos
}
