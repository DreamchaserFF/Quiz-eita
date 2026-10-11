<script lang="ts" setup>

    import { ref, computed } from 'vue'
    import { responderQuiz } from '../service/QuizService';
    import type { Pergunta, RespostaRequest } from '../types/QuizTypes'

const props = defineProps < { 
    perguntas: Pergunta[] 
    uuid: string
    } > ()

const indice = ref(0)
const selecionada = ref<string | null> (null)

const perguntaAtual = computed( () => props.perguntas[indice.value] )

const respostasDoUsuario : RespostaRequest = { uuid: props.uuid, respostas:[] }

const acertos = ref<number | null>(null)

function selecionar(alternativa: string) {
    selecionada.value=alternativa
}

function proxima() {
    respostasDoUsuario.respostas[indice.value] = {
        enunciado: perguntaAtual.value.enunciado, 
        resposta: selecionada.value!
    }

    indice.value++
    selecionada.value=null
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
                :class="{marcada: alternativa === selecionada}"
                @click="selecionar(alternativa)"
                >
                {{ alternativa }}
                </button>
            </li>
        </ul>
        <button :disabled="!selecionada" @click="proxima">Próxima</button>
    </div>
    <div v-else>
        <button @click="mandarRespostas">mandar respostas</button>
    </div>
    <div v-if="acertos !==null">
        <p>Quantidade de acertos: {{ acertos }}</p>
    </div>

</template>

<style scoped>


</style>