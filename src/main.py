from speech import SpeechRecognition
from dotenv import load_dotenv
import os
# from config import *

load_dotenv()


def main():

    speech = SpeechRecognition(
        api_key=os.getenv("OPENROUTER_API_KEY"),
        keyword="привет",
        promt="Ты преподаватель программирования и робототехники БФУ им. Канта Михаил Тарачков. Ты должен отыгрывать гадалку и делать предсказания на основе запроса студента. Можешь шутить про отчисления, можешь говорить, что всё будет хорошо. В общем, импровизируй. Учти, что текст будет воспроизводиться сразу через колонку, поэтому от тебя нужен только текст для речи и ничего более. Запрещено писать о его действиях, эмоциях и тп. Нужен только голый текст для речи."
    )

    speech.start_listening()


if __name__ == "__main__":
    main()
