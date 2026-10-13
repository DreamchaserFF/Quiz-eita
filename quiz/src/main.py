from app.graph.graph import graph
import asyncio

import json
import os

from infra.repository.redis_client import RedisClient
    
def main():
    result = graph.invoke({
          "tema": "Jogos",
          "quantidade": 2,
          "dificuldade": "facil",
          "perguntas": [],
      })

    dados = {
        **result,
        "perguntas": [
            pergunta.model_dump()
            for pergunta in result["perguntas"]
        ]
    }

    arquivo = os.path.join(
        "C:\\Users\\User\\Downloads\\Quiz-eita-main\\Quiz-eita-main\\quiz\\src\\presentation\\response.json"
    )

    with open(arquivo, "w", encoding="utf-8") as f:
        json.dump(
            dados,
            f,
            ensure_ascii=False,
            indent=4
        )


        
    #  redis_client = RedisClient()
    #  conn = redis_client.get_connection()

    #  async def test_redis():
    #      print(await conn.ping())


    #  asyncio.run(test_redis())


if __name__ == "__main__":
    main()




# import asyncio

# from infra.repository.redis_client import RedisClient
# from infra.repository.quiz_repository import QuizRepository


# async def main():
#     redis_client = RedisClient()
#     repository = QuizRepository(redis_client)

#      await repository.save("quiz:test", "processing")

#      result = await repository.get("quiz:test")

#      print(result)

#      await repository.delete("quiz:test")


<<<<<<< HEAD
# asyncio.run(main())
=======
#     asyncio.run(test_redis())


# if __name__ == "__main__":
#     main()




import asyncio

from infra.repository.redis_client import RedisClient
from infra.repository.quiz_repository import QuizRepository
from app.graph.node.retrive_context import retrieve_context

async def main():
    
    await retrieve_context({"context": []})

asyncio.run(main())
>>>>>>> 389ffb8e622b183c44c946be14181e9f63505c71



