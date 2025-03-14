import openai

# Azure OpenAI 설정
openai.api_type = "azure"
openai.api_base = "https://eunji-m85l0nou-eastus2.openai.azure.com/"
openai.api_version = "2024-10-21"
openai.api_key = "7MdTunS5kn1MaQXslloVqHKFr8d9s1rM6aNnzv83OC9rxYlq8Yh5JQQJ99BCACHYHv6XJ3w3AAAAACOGbeE6"

# 프롬프트 생성 및 API 호출
response = openai.ChatCompletion.create(
    engine="gpt-4o",
    messages=[{"role": "system", "content": "You are an AI assistant, which read a novel and analysis it. Read the novel and divide whole novel into 2~3 sections based on similar moods. Then, indicate which lines correspond to each mood in following format. For example, {'start': 1, 'end': 20, 'mood': ['exciting', 'joyful', 'peaceful']}. Don't give additional answer."},
              {"role": "user", "content": 
                  """
                  **The Mysterious Notebook**  

                    Lily loved collecting old books. One afternoon, she found a dusty, leather-bound notebook in a tiny antique shop. The owner smiled mysteriously as he handed it to her. “This one is special,” he said.  

                    Excited, Lily flipped through the pages. Strangely, they were all blank—except for the first page, which read: *Write your wish, and it will come true.*  

                    Skeptical but curious, she wrote: *I wish for a delicious chocolate cake.* Moments later, her mother called from the kitchen, “Lily! I made a surprise chocolate cake today!”  

                    Her heart raced. She tested it again. *I wish for a sunny day tomorrow.* The next morning, the rain cleared, and the sun shone brightly.  

                    Lily’s wishes kept coming true. She asked for small things at first—new books, good grades, little joys. But soon, she became bolder. *I wish to be the smartest student in school.* *I wish to win the lottery.* Every wish was granted.  

                    One night, she hesitated before writing her next wish. *I wish to know the truth about this notebook.* As soon as she finished writing, the room went dark.  

                    The pages flipped violently on their own. Words appeared in red ink: **"Every wish has a price."**  

                    Terrified, she tried to tear out the page, but the notebook wouldn’t budge. Suddenly, memories flashed before her eyes—moments she had forgotten. A classmate who had studied hard but lost to her in the competition. A neighbor who had bought the same lottery ticket but mysteriously lost it. Someone else had paid the price for her wishes.  

                    Shaking, Lily grabbed a pen and scribbled: *I wish to undo everything.*  

                    The notebook crumbled into dust in her hands. The next day, life returned to normal. She wasn’t the smartest in school anymore. She didn’t have endless luck. But for the first time in weeks, she felt free.  

                    Lily never sought shortcuts again. Some things, she realized, were meant to be earned—not wished for.
                  """
                  }],
    max_tokens=200
)

print(response["choices"][0]["message"]["content"])