<script lang="ts" setup>

    import { ref, computed } from 'vue'
    import { responderQuiz } from '../service/QuizService';
    import type { Pergunta, RespostaRequest } from '../types/QuizTypes'
    //Pergunta = { enunciado: string, alternativas: string[] }
    //RespostaRequest = { uuid: string, respostas: Resposta[] }
    //Resposta = { enunciado: string, resposta: string }

    //props que vem do SelectGame
const props = defineProps < { 
    perguntas: Pergunta[] 
    uuid: string
    } > ()

const emit = defineEmits< { (e: 'voltarMenu'): void } > ()
    
const indice = ref(0)
const alternativaSelecionada = ref<string | null> (null) 

    //muda a pergunta atual automaticamente conforme indice muda
const perguntaAtual = computed( () => props.perguntas[indice.value] ) 

const respostasDoUsuario : RespostaRequest = { uuid: props.uuid, respostas:[] }
const acertos = ref<number | null>(null)

const terminou = computed(() => indice.value >= props.perguntas.length)
const respostasEnviadas = ref(false)
const erro = ref('')

function selecionarAlternativa(alternativa: string) {
    alternativaSelecionada.value=alternativa
}

function proximaQuestao() {
    respostasDoUsuario.respostas.push ({
        enunciado: perguntaAtual.value.enunciado, 
        resposta: alternativaSelecionada.value!
    })

    indice.value++
    alternativaSelecionada.value=null
}

function voltarQuestao() {
    indice.value--
    alternativaSelecionada.value=null

}

async function mandarRespostas() {
    erro.value = ''
    respostasEnviadas.value=true

    try {
        const response = await responderQuiz(respostasDoUsuario)
        acertos.value = response
    }
    catch(e) {
        console.error(e)
        erro.value='Erro ao mandar respostas'
        respostasEnviadas.value = false

    }

}

</script>

<template>

    <div v-if="!terminou">
            <p>Pergunta {{ indice+1 }} de {{ perguntas.length }}</p>
            <h3>{{ perguntaAtual.enunciado }}</h3>
        
        <ul>

            <li v-for="alternativa in perguntaAtual.alternativas" :key="alternativa">

                <button
                :class="{marcada: alternativa === alternativaSelecionada}"
                @click="selecionarAlternativa(alternativa)"
                >
                {{ alternativa }}
                </button>

                
            </li>

        </ul>
        <button v-if="indice>=1" @click="voltarQuestao">Voltar</button>
        <button :disabled="!alternativaSelecionada" @click="proximaQuestao">Próxima</button>

    </div>

    <!--Usuario terminou todas as perguntas do quiz-->
    <div v-else>

        <button v-if="acertos === null" :disabled="respostasEnviadas" @click="mandarRespostas">
            mandar respostas
        </button>
        
        <p v-if="erro">{{ erro }}</p>
        <div v-else-if="respostasEnviadas">
            <p>{{ acertos === null ? 'Corrigindo...' : `Quantidade de acertos: ${acertos}`  }}</p>
            <button @click="emit('voltarMenu')">
                Voltar para menu
            </button>

        </div>

    </div>

</template>

<style scoped>


</style>