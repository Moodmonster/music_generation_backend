from flask import Blueprint, render_template, request
from azure.data.tables import TableClient
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta
import uuid
import requests

from openai import AzureOpenAI
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage, ImageContentItem, ImageUrl
from azure.core.credentials import AzureKeyCredential

import json
import re
from nltk.tokenize import sent_tokenize
import base64
import imghdr
from pydub import AudioSegment
import io
import asyncio

import sys
sys.path.append("/home/azureuser/music_generation_backend/src")
import config
from music_generation import create_and_compose

bp = Blueprint('contents', __name__, url_prefix="/contents")

contents_table = TableClient.from_connection_string(config.STORAGE_CONNECTION_STRING, "contents")
novel_table = TableClient.from_connection_string(config.STORAGE_CONNECTION_STRING, "novelEpisodes")
webtoon_table = TableClient.from_connection_string(config.STORAGE_CONNECTION_STRING, "webtoonEpisodes")
music_table = TableClient.from_connection_string(config.STORAGE_CONNECTION_STRING, "musics")

# 🔹 Blob 서비스 클라이언트 생성
blob_service_client = BlobServiceClient.from_connection_string(config.STORAGE_CONNECTION_STRING)

DALLE_client = AzureOpenAI(
    api_version="2024-02-01",
    azure_endpoint=config.IMAGE_API_ENDPOINT,
    api_key=config.IMAGE_API_KEY,
)

GPT_client = AzureOpenAI(  
    azure_endpoint=config.AI_API_BASE,  
    api_key=config.AI_API_KEY,  
    api_version="2024-05-01-preview",
)

PHI_client = ChatCompletionsClient(endpoint=config.AI_API_BASE+"models", credential=AzureKeyCredential(config.AI_API_KEY))

### get all list

@bp.route('/novel/all', methods=["GET"])
def getAllNovel():
    entities = contents_table.query_entities("PartitionKey eq 'novel'")
    
    result = []
    for entity in entities:
        result.append({
            "code": entity["RowKey"],
            "title": entity["Title"],
            "desc": entity["Description"],
            "author": entity["Author"],
            "userId": entity["UserId"],
            "contentType": "Novel",
            "clickCount": entity["ClickCount"],
            "thumbnailUrl": f"https://musicgenstorage.blob.core.windows.net/images/{entity["ThumbnailUrl"]}?{config.BLOB_SAS_KEY}"
        })
    
    return result

@bp.route('/webtoon/all', methods=["GET"])
def getAllWebtoon():
    entities = contents_table.query_entities("PartitionKey eq 'webtoon'")
    result = []
    for entity in entities:
        result.append({
            "code": entity["RowKey"],
            "title": entity["Title"],
            "desc": entity["Description"],
            "author": entity["Author"],
            "userId": entity["UserId"],
            "contentType": "Webtoon",
            "clickCount": entity["ClickCount"],
            "thumbnailUrl": f"https://musicgenstorage.blob.core.windows.net/images/{entity["ThumbnailUrl"]}?{config.BLOB_SAS_KEY}"
        })
    
    return result

### create new content

@bp.route('/novel/create', methods=["POST"])
def createNovel():
    data = request.get_json()
    
    blob_name = f"image_{str(uuid.uuid4())}.jpg"
    blob_client = blob_service_client.get_blob_client(container="images", blob=blob_name)

    result = DALLE_client.images.generate(
        model="dall-e-3",
        prompt=f"An illustration of the story '{data.get("title")}'. {data.get("desc")} Art Style: {data.get("prompt")}",
        n=1
    )

    image_url = json.loads(result.model_dump_json())['data'][0]['url']
    image_response = requests.get(image_url)
    
    blob_client.upload_blob(image_response.content, overwrite=True)
    
    entity = {
        "PartitionKey": "novel",
        "RowKey": str(uuid.uuid4()),
        "Title": data.get("title"),
        "Description": data.get("desc"),
        "Author": data.get("author"),
        "UserId": data.get("userId"),
        "ClickCount": 0,
        "ThumbnailUrl": blob_name
    }
    
    contents_table.upsert_entity(entity)
    
    return "Success"

@bp.route('/webtoon/create', methods=["POST"])
def createWebtoon():
    
    blob_name = f"image_{str(uuid.uuid4())}.jpg"
    blob_client = blob_service_client.get_blob_client(container="images", blob=blob_name)
    cover_image = request.files.get("file")
    blob_client.upload_blob(cover_image, overwrite=True)
    
    entity = {
        "PartitionKey": "webtoon",
        "RowKey": str(uuid.uuid4()),
        "Title": request.form.get("title"),
        "Description": request.form.get("desc"),
        "Author": request.form.get("author"),
        "UserId": request.form.get("userId"),
        "ClickCount": 0,
        "ThumbnailUrl": blob_name
    }
    
    contents_table.upsert_entity(entity)
    
    return "Success"

### delete content

@bp.route('/novel/delete', methods=["POST"])
def deleteNovel():
    data = request.get_json()
    contents_table.delete_entity(partition_key="novel", row_key=data.get("code"))
    
    entities = novel_table.query_entities(f"PartitionKey eq '{data.get("code")}'")
    for entity in entities:
        novel_table.delete_entity(partition_key=entity["PartitionKey"], row_key=entity["RowKey"])
    
    return "Success"

@bp.route('/webtoon/delete', methods=["POST"])
def deleteWebtoon():
    data = request.get_json()
    contents_table.delete_entity(partition_key="webtoon", row_key=data.get("code"))
    
    entities = webtoon_table.query_entities(f"PartitionKey eq '{data.get("code")}'")
    for entity in entities:
        webtoon_table.delete_entity(partition_key=entity["PartitionKey"], row_key=entity["RowKey"])
    
    return "Success"

### get episode list for specific content

@bp.route('/novel/episode/all', methods=["POST"])
def getNovel():
    data = request.get_json()
    contentCode = data.get("contentCode")
    entities = novel_table.query_entities(f"PartitionKey eq '{contentCode}'")
    
    result = []
    for entity in entities:
        result.append({
            "episodeCode": entity["Code"],
            "contentCode": entity["PartitionKey"],
            "epTitle": entity["Title"],
            "uploadDate": entity["UploadDate"]
        })
    
    return result

@bp.route('/webtoon/episode/all', methods=["POST"])
def getWebtoon():
    data = request.get_json()
    contentCode = data.get("contentCode")
    entities = webtoon_table.query_entities(f"PartitionKey eq '{contentCode}'")
    
    result = []
    for entity in entities:
        result.append({
            "episodeCode": entity["Code"],
            "contentCode": entity["PartitionKey"],
            "epTitle": entity["Title"],
            "uploadDate": entity["UploadDate"],
            "thumbnailUrl": f"https://musicgenstorage.blob.core.windows.net/images/{entity["ThumbnailUrl"]}?{config.BLOB_SAS_KEY}"
        })
    
    return result

### create episode

def tts(text):
    API_KEY = config.AI_API_KEY
    REGION = "eastus2"
    ENDPOINT = f"https://{REGION}.tts.speech.microsoft.com/cognitiveservices/v1"

    # 액세스 토큰 발급
    token_url = f"https://{REGION}.api.cognitive.microsoft.com/sts/v1.0/issuetoken"
    headers = {
        "Ocp-Apim-Subscription-Key": API_KEY,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    response = requests.post(token_url, headers=headers)
    access_token = response.text

    text = re.sub(r"[^\w\s,!.]", " ", text)
    # SSML (음성 설정)
    ssml_text = f"""
    <speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='en-US'>
        <voice name='en-US-JennyNeural'>
            {text}
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
    
    return response.content

@bp.route('/novel/episode/create', methods=["POST"])
def createNovelEpisode():
    episode = request.files.get("file").read().decode('utf-8')
    episode_line = sent_tokenize(episode)
    
    messages=[{"role": "system", "content": '''You are an AI assistant, which read a novel and analysis it. 
                Read the novel and divide whole novel into 2~4 sections based on similar moods. 
                Then, indicate which lines correspond to each mood in following format. 
                For example, {"start": 1, "end": 20, "mood": ["desperate", "tense", "rapid"]}\n{"start": 21, "end": 68, "mood": ["romantic", "peaceful"]}. 
                Don't give additional answer. There is total''' + str(len(episode_line)) + "lines."},
              {"role": "user", "content": episode}]
    
    completion = GPT_client.chat.completions.create(  
        model="gpt-4o",
        messages=messages,
        max_tokens=100
    )
    llm_response = completion.choices[0].message.content.split("\n")
    
    result = []
    for item in llm_response:
        item = json.loads(item)
        item["text"] = episode_line[item["start"]-1:item["end"]]
        tts_content = tts(" ".join(item["text"]))
        blob_client = blob_service_client.get_blob_client(container="tts", blob=f'tts_{str(uuid.uuid4())}.wav')
        blob_client.upload_blob(tts_content, overwrite=True)
        item["tts_url"] = blob_client.blob_name
        result.append(item)
    llm_response = {
        "data": result
    }
    entities = novel_table.query_entities(f"PartitionKey eq '{request.form.get("contentCode")}'")
    
    entity = {
        "PartitionKey": request.form.get("contentCode"),
        "RowKey": f"{len(list(entities)) + 1:03}",
        "Code": str(uuid.uuid4()),
        "Title": request.form.get("title"),
        "UploadDate": request.form.get("uploadDate")
    }
    
    blob_client = blob_service_client.get_blob_client(container="novels", blob=f'novel_{entity["Code"]}.json')
    blob_client.upload_blob(json.dumps(llm_response), overwrite=True)
    
    novel_table.upsert_entity(entity)
    
    return "Success", 200

@bp.route('/webtoon/episode/create', methods=["POST"])
def createWebtoonEpisode():
    files = request.files.getlist("images")
    
    captions = []
    names = []
    line = 1
    for file in files:
        if file.filename == "":
            continue

        blob_client = blob_service_client.get_blob_client(container="webtoons", blob=f'toon_{str(uuid.uuid4())}.jpg')
        blob_client.upload_blob(file.read(), overwrite=True)
        
        from urllib.request import urlopen, Request

        image_url = f"{blob_client.url}?{config.BLOB_SAS_KEY}"
        image_format = "jpeg"

        request_t = Request(image_url, headers={"User-Agent": "Mozilla/5.0"})
        image_data = base64.b64encode(urlopen(request_t).read()).decode("utf-8")
        data_url = f"data:image/{image_format};base64,{image_data}"

        response = PHI_client.complete(
            messages=[
                SystemMessage(content="You are a helpful assistant. You should create a simple, short caption about a cartoon images. Focus on describing the atmosphere."),
                UserMessage(content=[ImageContentItem(image_url=ImageUrl(url=data_url))]),
            ],
            model = "Phi-3.5-vision-instruct",
            max_tokens=200
        )
        
        captions.append(f"{line}. {response.choices[0].message.content}")
        names.append(blob_client.blob_name)
        line += 1
    
    messages=[{"role": "system", "content": '''You are an AI assistant, which read captions and analysis it. 
                Read the captions and divide into 2~4 sections based on similar moods. 
                Then, indicate which lines correspond to each mood in following format. 
                For example, {"start": 1, "end": 20, "mood": ["desperate", "tense", "rapid"]}\n{"start": 21, "end": 68, "mood": ["romantic", "peaceful"]}. 
                Don't give additional answer. There is total''' + str(len(captions)) + "lines."},
              {"role": "user", "content": "\n".join(captions)}]
    
    completion = GPT_client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=200
    )
    llm_response = completion.choices[0].message.content.split("\n")

    result = []
    for item in llm_response:
        item = json.loads(item)
        item["names"] = names[item["start"]-1:item["end"]]
        result.append(item)
    
    llm_response = {
        "data": result
    }
    entities = webtoon_table.query_entities(f"PartitionKey eq '{request.form.get("contentCode")}'")
    
    blob_client = blob_service_client.get_blob_client(container="images", blob=f'image_{str(uuid.uuid4())}.jpg')
    blob_client.upload_blob(request.files.get("thumbnailImage").read(), overwrite=True)
    
    entity = {
        "PartitionKey": request.form.get("contentCode"),
        "RowKey": f"{len(list(entities)) + 1:03}",
        "Code": str(uuid.uuid4()),
        "Title": request.form.get("title"),
        "UploadDate": request.form.get("uploadDate"),
        "Images": json.dumps(llm_response),
        "ThumbnailUrl": blob_client.blob_name
    }
    
    webtoon_table.upsert_entity(entity)
    
    return "Success"

### get episode

def combine_tts_bgm(tts, bgm):
    if len(tts) < len(bgm):
        bgm = bgm[:len(tts)]
        bgm = bgm.fade_out(2000)
    else:
        bgm_repeated = bgm * (len(tts)//len(bgm))
        remaining_length = len(tts) - len(bgm_repeated)
        bgm = bgm_repeated + bgm[:remaining_length]
    
    bgm = bgm - 10
    result = tts.overlay(bgm)
    return result

@bp.route('/novel/episode/paragraphs', methods=["POST"])
def getNovelEpisode():
    data = request.get_json()
    entities = novel_table.query_entities(f"Code eq '{data.get("episodeCode")}'")
    entity = list(entities)[0]
    
    blob_client = blob_service_client.get_blob_client(container="novels", blob=f"novel_{data.get("episodeCode")}.json")
    
    blob_data = blob_client.download_blob().readall()
    json_data = json.loads(blob_data)
            
    results = []
    order = 0
    combined = AudioSegment.empty()
    for item in json_data["data"]:
        
        music_entities = music_table.query_entities(f"mood eq '{", ".join(item["mood"])}, {data.get("prompt")}'")
        music_entity = list(music_entities)
        
        if len(music_entity):
            music_url = f"https://musicgenstorage.blob.core.windows.net/musics/music_{music_entity[0]["RowKey"]}.wav?{config.BLOB_SAS_KEY}"
            music_name = f"music_{music_entity[0]["RowKey"]}.wav"
        else:
            music_file = asyncio.run(create_and_compose(f"A 30 second background music, {", ".join(item["mood"])}, {data.get("prompt")}"))
            music_id = str(uuid.uuid4())
            blob_name = f"music_{music_id}.wav"
            blob_client = blob_service_client.get_blob_client(container="musics", blob=blob_name)
            blob_client.upload_blob(music_file, overwrite=True)
            music_table.upsert_entity({
                "PartitionKey": "music",
                "RowKey": music_id,
                "mood": f'{", ".join(item["mood"])}, {data.get("prompt")}'
            })
            music_url = f"https://musicgenstorage.blob.core.windows.net/musics/{blob_name}?{config.BLOB_SAS_KEY}"
            music_name = blob_name
        
        blob_client = blob_service_client.get_blob_client(container="tts", blob=item["tts_url"])
        tts = AudioSegment.from_wav(io.BytesIO(blob_client.download_blob().readall()))
        blob_client = blob_service_client.get_blob_client(container="musics", blob=music_name)
        bgm = AudioSegment.from_wav(io.BytesIO(blob_client.download_blob().readall()))
        combined += combine_tts_bgm(tts, bgm)
        
        results.append({
            "text": " ".join(item["text"]),
            "music_url": music_url,
            "displayOrder": order
        })
        order += 1
    
    buffer = io.BytesIO()
    combined.export(buffer, format="wav")
    buffer.seek(0)
    blob_name = f"merged_tts_{uuid.uuid4()}.wav"
    blob_client = blob_service_client.get_blob_client(container="tts", blob=blob_name)

    blob_client.upload_blob(buffer, overwrite=True)
    
    results = {
        "data": results,
        "ttsUrl": f"{blob_client.url}?{config.BLOB_SAS_KEY}"
    }
    
    return results

@bp.route('/webtoon/episode/paragraphs', methods=["POST"])
def getWebtoonEpisode():
    data = request.get_json()
    entities = webtoon_table.query_entities(f"Code eq '{data.get("episodeCode")}'")
    entity = list(entities)[0]
    
    json_data = json.loads(entity["Images"])
            
    results = []
    order = 0
    for item in json_data["data"]:
        music_entities = music_table.query_entities(f"mood eq '{", ".join(item["mood"])}, {data.get("prompt")}'")
        music_entity = list(music_entities)
        
        if len(music_entity):
            music_url = f"https://musicgenstorage.blob.core.windows.net/musics/music_{music_entity[0]["RowKey"]}.wav?{config.BLOB_SAS_KEY}"
        else:
            music_file = asyncio.run(create_and_compose(f"A 30 second background music, {", ".join(item["mood"])}, {data.get("prompt")}"))
            music_id = str(uuid.uuid4())
            blob_name = f"music_{music_id}.wav"
            blob_client = blob_service_client.get_blob_client(container="musics", blob=blob_name)
            blob_client.upload_blob(music_file, overwrite=True)
            music_table.upsert_entity({
                "PartitionKey": "music",
                "RowKey": music_id,
                "mood": f'{", ".join(item["mood"])}, {data.get("prompt")}'
            })
            music_url = f"https://musicgenstorage.blob.core.windows.net/musics/{blob_name}?{config.BLOB_SAS_KEY}"
        
        results.append({
            "images": [f"https://musicgenstorage.blob.core.windows.net/webtoons/{image}?{config.BLOB_SAS_KEY}" for image in item["names"]],
            "music_url": music_url,
            "displayOrder": order
        })
        order += 1
        
    results = {
        "data": results
    }
    
    return results

### delete specific episode

@bp.route('/novel/episode/delete', methods=["POST"])
def deleteNovelEpisode():
    data = request.get_json()
    entities = novel_table.query_entities(f"Code eq '{data.get("code")}'")
    for entity in entities:
        novel_table.delete_entity(partition_key=entity["PartitionKey"], row_key=entity["RowKey"])
    
    return "Success"

@bp.route('/webtoon/episode/delete', methods=["POST"])
def deleteWebtoonEpisode():
    data = request.get_json()
    entities = webtoon_table.query_entities(f"Code eq '{data.get("code")}'")
    for entity in entities:
        webtoon_table.delete_entity(partition_key=entity["PartitionKey"], row_key=entity["RowKey"])
    
    return "Success"

### Update ClickCount

@bp.route('/updateCount', methods=["POST"])
def updateClickCount():
    data = request.get_json()
    entity = contents_table.get_entity(partition_key=("novel" if data.get("contentType")=="Novel" else "webtoon"), row_key=data.get("code"))
    entity["ClickCount"] = entity["ClickCount"] + 1
    contents_table.update_entity(entity=entity)
    
    return "Success"