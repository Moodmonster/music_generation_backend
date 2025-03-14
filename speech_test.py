import requests

# Azure Speech API 정보 설정
API_KEY = "7MdTunS5kn1MaQXslloVqHKFr8d9s1rM6aNnzv83OC9rxYlq8Yh5JQQJ99BCACHYHv6XJ3w3AAAAACOGbeE6"  # Azure에서 발급받은 API 키
REGION = "eastus2"  # 예: eastus, koreacentral
ENDPOINT = f"https://{REGION}.tts.speech.microsoft.com/cognitiveservices/v1"

# 액세스 토큰 발급
token_url = f"https://{REGION}.api.cognitive.microsoft.com/sts/v1.0/issuetoken"
headers = {
    "Ocp-Apim-Subscription-Key": API_KEY,
    "Content-Type": "application/x-www-form-urlencoded"
}
response = requests.post(token_url, headers=headers)
access_token = response.text

# SSML (음성 설정)
ssml_text = """
<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='en-US'>
    <voice name='en-US-JennyNeural'>
        Hello! I'm happy to assist you.
    </voice>
</speak>
"""


# 요청 헤더
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/ssml+xml",
    "X-Microsoft-OutputFormat": "riff-24khz-16bit-mono-pcm"  # WAV 형식
}

# TTS 요청
response = requests.post(ENDPOINT, headers=headers, data=ssml_text)

# 음성 파일 저장
if response.status_code == 200:
    with open("output.wav", "wb") as f:
        f.write(response.content)
    print("✅ TTS 성공! 'output.wav' 파일이 저장되었습니다.")
else:
    print(f"❌ 오류 발생: {response.status_code}, {response.text}")
