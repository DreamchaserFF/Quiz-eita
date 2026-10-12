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
    
const indice = ref(0)
const alternativaSelecionada = ref<string | null> (null) 

    //muda a pergunta atual automaticamente conforme indice muda
const perguntaAtual = computed( () => props.perguntas[indice.value] ) 

const respostasDoUsuario : RespostaRequest = { uuid: props.uuid, respostas:[] }
const acertos = ref<number | null>(null)

function selecionarAlternativa(alternativa: string) {
    alternativaSelecionada.value=alternativa
}

function proximaQuestao() {
    respostasDoUsuario.respostas[indice.value] = {
        enunciado: perguntaAtual.value.enunciado, 
        resposta: alternativaSelecionada.value!
    }

    indice.value++
    alternativaSelecionada.value=null
}

async function mandarRespostas() {

    try {
        const response = await responderQuiz(respostasDoUsuario)
        acertos.value = response
    }
    catch(e) {console.error(e)}

}

</script>

<template>

    <div v-if="perguntaAtual">
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

        <button :disabled="!alternativaSelecionada" @click="proximaQuestao">Próxima</button>

    </div>

    <div v-else>

        <button @click="mandarRespostas">mandar respostas</button>

    </div>

    <!--Mostrar quantidade de acertos depois de enviar as respostas-->
    <div v-if="acertos !==null">

        <p>Quantidade de acertos: {{ acertos }}</p>

    </div>

</template>

<style scoped>


</style>