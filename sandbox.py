from audible import log_helper
import audible
from httpx import Response
import requests
from pydub import AudioSegment
import ffmpeg

AUDIBLE_URL_BASE = "https://www.audible"


log_helper.set_console_logger("debug")

country_code_mapping = {
    "us": ".com",
    "ca": ".ca",
    "uk": ".co.uk",
    "au": ".co.au",
    "fr": ".fr",
    "de": ".de",
    "jp": ".co.jp",
    "it": ".it",
    "in": ".co.in",
    "es": ".es"
}

# if not
auth = audible.Authenticator.from_file("credentials.json")

# ATOMIC HABITS: 1473565421
# THINK AGAIN: 0593394763

COUNTRY_CODE = "uk"
ASIN = "1473565421"
START_POSITION_OFFSET = 10000
END_POSITION_OFFSET = 0

content_url = f"/1.0/content/{ASIN}/licenserequest"


def generate_url(country_code, url_type, asin=None):
    if asin and url_type == "download":
        return f"{AUDIBLE_URL_BASE}{country_code_mapping.get(country_code)}/library/download?asin={asin}&codec=AAX_44_128"


def get(url, **kwargs):
    with audible.Client(auth=auth, response_callback=Response) as client:
        library = client.get(
            url,
            **kwargs
        )
        print(library)
        breakpoint()
        return library.url


bookmarks_url = f"https://cde-ta-g7g.amazon.com/FionaCDEServiceEngine/sidecar?type=AUDI&key={ASIN}"


def get_bookmarks(url, asin, **kwargs):
    with audible.Client(auth=auth) as client:
        library = client.get(
            url,
            **kwargs
        )
        slice_bookmarks(library.get("payload").get("records"))


def slice_bookmarks(li_bookmarks):
    li_clips = sorted(li_bookmarks, key=lambda i: i["type"], reverse=True)
    print(li_clips)
    audio_book = AudioSegment.from_wav("file_name.wav")
    file_counter = 1
    for audio_clip in li_clips:
        notes_dict = {}
        raw_start_pos = int(audio_clip["startPosition"])
        if audio_clip.get("type", None) in ["audible.note"]:
            notes_dict[raw_start_pos] = audio_clip.get("text")

        if audio_clip.get("type", None) in ["audible.clip", "audible.bookmark"]:

            start_pos = raw_start_pos - START_POSITION_OFFSET
            end_pos = int(audio_clip.get(
                "endPosition", raw_start_pos + 30000)) + END_POSITION_OFFSET
            if start_pos == end_pos:
                end_pos += 30000

            clip = audio_book[start_pos:end_pos]

            file_name = notes_dict.get(raw_start_pos, f"clip{file_counter}")

            clip.export(f"clips/atomichabits/{file_name}.flac", format="flac")
            file_counter += 1


def convert_aax(aax_file):
    aax_instance = ffmpeg.input(aax_file)
    (
        ffmpeg
        .overlay(aax_instance.hflip())
        .drawbox(50, 50, 120, 120, color='red', thickness=5)
        .output('out.mp4')
        .run()
    )

# bookmarks_dict = get_bookmarks(bookmarks_url, ASIN, num_results=1000, response_groups="product_desc, product_attrs")


# DOWNLOAD
print(generate_url(COUNTRY_CODE, "download", ASIN))
sample_url = ""
re = get(generate_url(COUNTRY_CODE, "download", ASIN),
         num_results=1000, response_groups="product_desc, product_attrs")

audible_response = requests.get(re)

if audible_response.ok:
    with open('thinkagain.aax', 'wb') as f:
        f.write(audible_response.content)

else:
    print(audible_response.text)