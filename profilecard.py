from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import requests
from io import BytesIO
import numpy as np

# Text Setup
font = ImageFont.truetype('assets/segoe-ui-bold.ttf', 120)
statfont = ImageFont.truetype('assets/segoe-ui-bold.ttf', 80)
textx, texty = 150, 0
# Icon Setup
iconsize = 400
shadowsize = 40
iconx, icony, = 100, 200
# Load Images on Start
global mask, bgus, shadow, blackbgus, globe, crown
mask = Image.open("assets/transparencymask.png").convert("RGBA")
bg = Image.open("assets/transbg.png").convert("RGBA")
shadow = Image.open("assets/shadow.png").convert("RGBA")
blackbg = Image.open("assets/roundedbgtrans.png").convert("RGBA")
globe = Image.open("assets/globe.png").convert("RGBA")
crown = Image.open("assets/crown.png").convert("RGBA")

async def makecard(profile):

    text = profile.player_name

    headsetcol = {
    0: (234, 118, 22),
    1: (255, 255, 255),
    16: (71, 200, 255),
    32: (255, 89, 255),
    256: (18, 168, 174),
    37: (255, 255, 255),
    2: (0, 177, 230),
    4: (255, 255, 255),
    128: (181, 0, 178),
    47: (237, 62, 55),
    35: (199, 105, 238),
    36: (204, 56, 236),
    51: (63, 219, 167),
}
    
    headsetnme = {
    0: "Unknown",
    1: "Rift",
    16: "Rift S",
    32: "Quest",
    256: "Quest 2",
    512: "Quest 3",
    2: "Vive",
    4: "Vive Pro",
    128: "Vive Cosmos",
    8: "Windows Mixed Reality",
    33: "Pico Neo 3",
    34: "Pico Neo 2",
    35: "Vive Pro 2",
    36: "Vive Elite",
    37: "Miramar",
    38: "Pimax 8K",
    39: "Pimax 5K",
    40: "Pimax Artisan",
    41: "HP Reverb",
    42: "Samsung WMR",
    43: "Qiyu Dream",
    44: "Disco",
    45: "Lenovo Explorer",
    46: "Acer WMR",
    47: "Vive Focus",
    48: "Arpara",
    49: "Dell Visor",
    50: "E3",
    51: "Vive DVT",
    52: "Glasses 20",
    53: "Varjo",
    54: "Vaporeon",
    55: "Huawei VR",
    56: "Asus WMR",
    57: "CloudXR",
    58: "VRidge",
    59: "Medion",
    60: "Pico Neo 4",
    61: "Quest Pro",
    62: "Pimax Crystal",
    63: "E4",
    64: "Valve Index",
    65: "Controllable"
}
    
    headsetimg = {
    64: "index.png",
    1: "oculus.png",
    16: "oculus.png",
    32: "oculus.png",
    256: "oculus.png",
    37: "oculus.png",
    61: "meta.png",
    512: "meta3.png",
    2: "vive.png",
    4: "vive.png",
    128: "vive.png",
    47: "vive.png",
    35: "vive.png",
    36: "vive.png",
    8: "wmr.png",
    33: "pico.png",
    34: "pico.png",
    38: "pimax.png",
    39: "pimax.png",
    40: "pimax.png",
    41: "hp.pmg",
    42: "samsung.png",
    43: "iqiyi.png",
    44: "disco.png",
    45: "lenovo.png",
    46: "acer.png",
    48: "arpara.png",
    49: "dell.png",
    51: "vive.png",
    53: "varjo.png",
    55: "huawei.png",
    56: "asus.png",
    60: "pico.png",
    62: "pimax.png",
    65: "controllable.png"
    }

    headsetpng = f'assets/headsets/{headsetimg.get(profile.hmd, "unknown.png")}'
    headsetname = headsetnme.get(profile.hmd, "Unknown HMD")

    avatarresponse = requests.get(profile.avatar)
    if avatarresponse.status_code == 200:
        # Image setups and stuff
        pfpdata = BytesIO(avatarresponse.content)
        pfp = Image.open(pfpdata).convert("RGBA")
        flag = Image.open(f"assets/flags/{profile.country.lower()}.png").convert("RGBA")
        # Headset Coloring
        if headsetpng == "assets/headsets/vive.png" or headsetpng == "assets/headsets/oculus.png":
            headsetnoc = Image.open(headsetpng).convert("RGBA")
            data = np.array(headsetnoc)
            red, green, blue, alpha = data.T
            white_areas = (red == 255) & (blue == 255) & (green == 255)
            data[..., :-1][white_areas.T] = headsetcol.get(profile.hmd, (255, 255, 255))
            headset = Image.fromarray(data)
        else:
            headset = Image.open(headsetpng).convert("RGBA")
        if profile.cover is None:
            bg.paste(blackbg, (0, 0), blackbg)
        # Player Cover
        if profile.cover is not None:
            coverresponse = requests.get(profile.cover)
            if coverresponse.status_code == 200:
                coverdata = BytesIO(coverresponse.content)
                coveralpha = blackbg.split()[3]
                cover = Image.open(coverdata).convert("RGBA")
                if int(cover.size[0]) / int(cover.size[1]) > 5:
                    cover = cover.crop(((int(cover.size[0] / 8)), 0, (int((cover.size[0] / 6.5) * 2)), cover.size[1]))
                coveralph = cover.resize((2000, 1100), resample=Image.BILINEAR)
                coverfin = coveralph.filter(ImageFilter.GaussianBlur(5))
                covercrop = coverfin.crop((0, 0, 2000, 700))
                covercrop.putalpha(coveralpha)
                coverdark = ImageEnhance.Brightness(covercrop)
                coverfinal = coverdark.enhance(0.5)
                bg.paste(coverfinal, (0, 0), coverfinal)
        # Crop PFP to have rounded corners
        resized_target = pfp.resize(mask.size, resample=Image.BILINEAR)
        target_alpha = mask.split()[3]
        result_image = resized_target.copy()
        result_image.putalpha(target_alpha)
        # Player Icon
        resizedimg = result_image.resize((iconsize, iconsize), resample=Image.BILINEAR)
        shadowresize = shadow.resize(((iconsize + shadowsize), (iconsize + shadowsize)), resample=Image.BILINEAR)
        bg.paste(shadowresize, (int(iconx - shadowsize / 2), int(icony - shadowsize / 2)), shadowresize)
        bg.paste(resizedimg, (iconx, icony), resizedimg)
        # Headset
        headsetsize = 50 if profile.hmd == 42 else 30 if profile.hmd in [2, 4, 128, 35, 36, 47] else 10 if profile.hmd in [60, 33, 34] else 0 # Samsung WMR, Vive, Pico # This is such a stupid fucking problem why are so many flags tall and so many headset icons tall?
        headsetx = (550 + (headsetsize / 2))
        headsety = (440 + (headsetsize / 2))
        headsetresize = headset.resize(((150 - headsetsize), (150 - headsetsize)), resample=Image.BILINEAR)
        bg.paste(headsetresize, (int(headsetx), int(headsety)), headsetresize)
        # Flag
        flagres = flag.resize(tuple([int(0.5*x) for x in flag.size]), resample=Image.BILINEAR)
        bg.paste(flagres, (545, 350), flagres)
        # Globe
        globeres = globe.resize((120, 120), resample=Image.BILINEAR)
        bg.paste(globeres, (565, 205), globeres)
        # Owner Crown
        if profile.mapperId == 144998:
            crownres = crown.resize((120, 120), resample=Image.BILINEAR)
            bg.paste(crownres, (20, 20), crownres)
        # Player Name and Stats
        bgdraw = ImageDraw.Draw(bg, mode="RGBA")
        size_width = bgdraw.textlength(text, font=font)
        textx = max((iconsize / 2 + iconx) - (size_width / 2), 50)
        bgdraw.text((textx, texty), text, fill=(255, 255, 255), font=font, stroke_width=4, stroke_fill="black")
        bgdraw.text((730, 456), headsetname, fill="white", font=statfont)
        bgdraw.text((730, 337), f"#{profile.country_rank}", fill="white", font=statfont)
        bgdraw.text((730, 200), f"#{profile.rank}", fill="white", font=statfont)
        img_byte_array = BytesIO()
        bg.save(img_byte_array, format="PNG")
        img_byte_array.seek(0)

        return img_byte_array

    else:
        print("some kind of error lol")