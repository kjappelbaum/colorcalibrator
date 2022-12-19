# -*- coding: utf-8 -*-
"""Some utility functions"""
import json

import colour
import dash_core_components as dcc
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from colormath.color_conversions import convert_color
from colormath.color_diff import delta_e_cie2000
from colormath.color_objects import LabColor, sRGBColor
from colour_checker_detection import detect_colour_checkers_segmentation
from PIL import Image, ImageOps
from plotly.subplots import make_subplots
from loguru import logger

import numpy


def patch_asscalar(a):
    return a.item()


setattr(numpy, "asscalar", patch_asscalar)

# [filename, image_signature, action_stack]
STORAGE_PLACEHOLDER = json.dumps(
    {"filename": None, "image_signature": None, "action_stack": [], "image_string": ""}
)

GRAPH_PLACEHOLDER = dcc.Graph(id="interactive-image", style={"height": "80vh"})

# https://www.datacolor.com/wp-content/uploads/2018/01/SpyderCheckr_Color_Data_V2.pdf
TARGET_SPYDER24 = (
    np.array(
        [
            [43, 41, 43],  # 6E
            [80, 80, 78],  # 5E
            [122, 118, 116],  # 4E
            [161, 157, 154],  # 3E
            [202, 198, 195],  # 2E
            [249, 242, 238],  # 1E
            [25, 55, 135],  # 6F
            [57, 146, 64],  # 5F
            [186, 26, 51],  # 4F
            [245, 205, 0],  # 3F
            [192, 75, 145],  # 2F
            [0, 127, 159],  # 1F
            [238, 158, 25],  # 6G
            [157, 188, 54],  # 5G
            [83, 58, 106],  # 4G
            [195, 79, 95],  # 3G
            [58, 88, 159],  # 2G
            [222, 118, 32],  # 1G
            [112, 76, 60],  # 6H
            [197, 145, 125],  # 5H
            [87, 120, 155],  # 4H
            [82, 106, 60],  # 3H
            [126, 125, 174],  # 2H
            [98, 187, 166],  # 1H
        ]
    )
    / 255
)

XKCD_RGB_DICT = {
    "cloudy blue": (172, 194, 217),
    "dark pastel green": (86, 174, 87),
    "dust": (178, 153, 110),
    "electric lime": (168, 255, 4),
    "fresh green": (105, 216, 79),
    "light eggplant": (137, 69, 133),
    "nasty green": (112, 178, 63),
    "really light blue": (212, 255, 255),
    "tea": (101, 171, 124),
    "warm purple": (149, 46, 143),
    "yellowish tan": (252, 252, 129),
    "cement": (165, 163, 145),
    "dark grass green": (56, 128, 4),
    "dusty teal": (76, 144, 133),
    "grey teal": (94, 155, 138),
    "macaroni and cheese": (239, 180, 53),
    "pinkish tan": (217, 155, 130),
    "spruce": (10, 95, 56),
    "strong blue": (12, 6, 247),
    "toxic green": (97, 222, 42),
    "windows blue": (55, 120, 191),
    "blue blue": (34, 66, 199),
    "blue with a hint of purple": (83, 60, 198),
    "booger": (155, 181, 60),
    "bright sea green": (5, 255, 166),
    "dark green blue": (31, 99, 87),
    "deep turquoise": (1, 115, 116),
    "green teal": (12, 181, 119),
    "strong pink": (255, 7, 137),
    "bland": (175, 168, 139),
    "deep aqua": (8, 120, 127),
    "lavender pink": (221, 133, 215),
    "light moss green": (166, 200, 117),
    "light seafoam green": (167, 255, 181),
    "olive yellow": (194, 183, 9),
    "pig pink": (231, 142, 165),
    "deep lilac": (150, 110, 189),
    "desert": (204, 173, 96),
    "dusty lavender": (172, 134, 168),
    "purpley grey": (148, 126, 148),
    "purply": (152, 63, 178),
    "candy pink": (255, 99, 233),
    "light pastel green": (178, 251, 165),
    "boring green": (99, 179, 101),
    "kiwi green": (142, 229, 63),
    "light grey green": (183, 225, 161),
    "orange pink": (255, 111, 82),
    "tea green": (189, 248, 163),
    "very light brown": (211, 182, 131),
    "egg shell": (255, 252, 196),
    "eggplant purple": (67, 5, 65),
    "powder pink": (255, 178, 208),
    "reddish grey": (153, 117, 112),
    "baby shit brown": (173, 144, 13),
    "liliac": (196, 142, 253),
    "stormy blue": (80, 123, 156),
    "ugly brown": (125, 113, 3),
    "custard": (255, 253, 120),
    "darkish pink": (218, 70, 125),
    "deep brown": (65, 2, 0),
    "greenish beige": (201, 209, 121),
    "manilla": (255, 250, 134),
    "off blue": (86, 132, 174),
    "battleship grey": (107, 124, 133),
    "browny green": (111, 108, 10),
    "bruise": (126, 64, 113),
    "kelley green": (0, 147, 55),
    "sickly yellow": (208, 228, 41),
    "sunny yellow": (255, 249, 23),
    "azul": (29, 93, 236),
    "darkgreen": (5, 73, 7),
    "green/yellow": (181, 206, 8),
    "lichen": (143, 182, 123),
    "light light green": (200, 255, 176),
    "pale gold": (253, 222, 108),
    "sun yellow": (255, 223, 34),
    "tan green": (169, 190, 112),
    "burple": (104, 50, 227),
    "butterscotch": (253, 177, 71),
    "toupe": (199, 172, 125),
    "dark cream": (255, 243, 154),
    "indian red": (133, 14, 4),
    "light lavendar": (239, 192, 254),
    "poison green": (64, 253, 20),
    "baby puke green": (182, 196, 6),
    "bright yellow green": (157, 255, 0),
    "charcoal grey": (60, 65, 66),
    "squash": (242, 171, 21),
    "cinnamon": (172, 79, 6),
    "light pea green": (196, 254, 130),
    "radioactive green": (44, 250, 31),
    "raw sienna": (154, 98, 0),
    "baby purple": (202, 155, 247),
    "cocoa": (135, 95, 66),
    "light royal blue": (58, 46, 254),
    "orangeish": (253, 141, 73),
    "rust brown": (139, 49, 3),
    "sand brown": (203, 165, 96),
    "swamp": (105, 131, 57),
    "tealish green": (12, 220, 115),
    "burnt siena": (183, 82, 3),
    "camo": (127, 143, 78),
    "dusk blue": (38, 83, 141),
    "fern": (99, 169, 80),
    "old rose": (200, 127, 137),
    "pale light green": (177, 252, 153),
    "peachy pink": (255, 154, 138),
    "rosy pink": (246, 104, 142),
    "light bluish green": (118, 253, 168),
    "light bright green": (83, 254, 92),
    "light neon green": (78, 253, 84),
    "light seafoam": (160, 254, 191),
    "tiffany blue": (123, 242, 218),
    "washed out green": (188, 245, 166),
    "browny orange": (202, 107, 2),
    "nice blue": (16, 122, 176),
    "sapphire": (33, 56, 171),
    "greyish teal": (113, 159, 145),
    "orangey yellow": (253, 185, 21),
    "parchment": (254, 252, 175),
    "straw": (252, 246, 121),
    "very dark brown": (29, 2, 0),
    "terracota": (203, 104, 67),
    "ugly blue": (49, 102, 138),
    "clear blue": (36, 122, 253),
    "creme": (255, 255, 182),
    "foam green": (144, 253, 169),
    "grey/green": (134, 161, 125),
    "light gold": (253, 220, 92),
    "seafoam blue": (120, 209, 182),
    "topaz": (19, 187, 175),
    "violet pink": (251, 95, 252),
    "wintergreen": (32, 249, 134),
    "yellow tan": (255, 227, 110),
    "dark fuchsia": (157, 7, 89),
    "indigo blue": (58, 24, 177),
    "light yellowish green": (194, 255, 137),
    "pale magenta": (215, 103, 173),
    "rich purple": (114, 0, 88),
    "sunflower yellow": (255, 218, 3),
    "green/blue": (1, 192, 141),
    "leather": (172, 116, 52),
    "racing green": (1, 70, 0),
    "vivid purple": (153, 0, 250),
    "dark royal blue": (2, 6, 111),
    "hazel": (142, 118, 24),
    "muted pink": (209, 118, 143),
    "booger green": (150, 180, 3),
    "canary": (253, 255, 99),
    "cool grey": (149, 163, 166),
    "dark taupe": (127, 104, 78),
    "darkish purple": (117, 25, 115),
    "true green": (8, 148, 4),
    "coral pink": (255, 97, 99),
    "dark sage": (89, 133, 86),
    "dark slate blue": (33, 71, 97),
    "flat blue": (60, 115, 168),
    "mushroom": (186, 158, 136),
    "rich blue": (2, 27, 249),
    "dirty purple": (115, 74, 101),
    "greenblue": (35, 196, 139),
    "icky green": (143, 174, 34),
    "light khaki": (230, 242, 162),
    "warm blue": (75, 87, 219),
    "dark hot pink": (217, 1, 102),
    "deep sea blue": (1, 84, 130),
    "carmine": (157, 2, 22),
    "dark yellow green": (114, 143, 2),
    "pale peach": (255, 229, 173),
    "plum purple": (78, 5, 80),
    "golden rod": (249, 188, 8),
    "neon red": (255, 7, 58),
    "old pink": (199, 121, 134),
    "very pale blue": (214, 255, 254),
    "blood orange": (254, 75, 3),
    "grapefruit": (253, 89, 86),
    "sand yellow": (252, 225, 102),
    "clay brown": (178, 113, 61),
    "dark blue grey": (31, 59, 77),
    "flat green": (105, 157, 76),
    "light green blue": (86, 252, 162),
    "warm pink": (251, 85, 129),
    "dodger blue": (62, 130, 252),
    "gross green": (160, 191, 22),
    "ice": (214, 255, 250),
    "metallic blue": (79, 115, 142),
    "pale salmon": (255, 177, 154),
    "sap green": (92, 139, 21),
    "algae": (84, 172, 104),
    "bluey grey": (137, 160, 176),
    "greeny grey": (126, 160, 122),
    "highlighter green": (27, 252, 6),
    "light light blue": (202, 255, 251),
    "light mint": (182, 255, 187),
    "raw umber": (167, 94, 9),
    "vivid blue": (21, 46, 255),
    "deep lavender": (141, 94, 183),
    "dull teal": (95, 158, 143),
    "light greenish blue": (99, 247, 180),
    "mud green": (96, 102, 2),
    "pinky": (252, 134, 170),
    "red wine": (140, 0, 52),
    "shit green": (117, 128, 0),
    "tan brown": (171, 126, 76),
    "darkblue": (3, 7, 100),
    "rosa": (254, 134, 164),
    "lipstick": (213, 23, 78),
    "pale mauve": (254, 208, 252),
    "claret": (104, 0, 24),
    "dandelion": (254, 223, 8),
    "orangered": (254, 66, 15),
    "poop green": (111, 124, 0),
    "ruby": (202, 1, 71),
    "dark": (27, 36, 49),
    "greenish turquoise": (0, 251, 176),
    "pastel red": (219, 88, 86),
    "piss yellow": (221, 214, 24),
    "bright cyan": (65, 253, 254),
    "dark coral": (207, 82, 78),
    "algae green": (33, 195, 111),
    "darkish red": (169, 3, 8),
    "reddy brown": (110, 16, 5),
    "blush pink": (254, 130, 140),
    "camouflage green": (75, 97, 19),
    "lawn green": (77, 164, 9),
    "putty": (190, 174, 138),
    "vibrant blue": (3, 57, 248),
    "dark sand": (168, 143, 89),
    "purple/blue": (93, 33, 208),
    "saffron": (254, 178, 9),
    "twilight": (78, 81, 139),
    "warm brown": (150, 78, 2),
    "bluegrey": (133, 163, 178),
    "bubble gum pink": (255, 105, 175),
    "duck egg blue": (195, 251, 244),
    "greenish cyan": (42, 254, 183),
    "petrol": (0, 95, 106),
    "royal": (12, 23, 147),
    "butter": (255, 255, 129),
    "dusty orange": (240, 131, 58),
    "off yellow": (241, 243, 63),
    "pale olive green": (177, 210, 123),
    "orangish": (252, 130, 74),
    "leaf": (113, 170, 52),
    "light blue grey": (183, 201, 226),
    "dried blood": (75, 1, 1),
    "lightish purple": (165, 82, 230),
    "rusty red": (175, 47, 13),
    "lavender blue": (139, 136, 248),
    "light grass green": (154, 247, 100),
    "light mint green": (166, 251, 178),
    "sunflower": (255, 197, 18),
    "velvet": (117, 8, 81),
    "brick orange": (193, 74, 9),
    "lightish red": (254, 47, 74),
    "pure blue": (2, 3, 226),
    "twilight blue": (10, 67, 122),
    "violet red": (165, 0, 85),
    "yellowy brown": (174, 139, 12),
    "carnation": (253, 121, 143),
    "muddy yellow": (191, 172, 5),
    "dark seafoam green": (62, 175, 118),
    "deep rose": (199, 71, 103),
    "dusty red": (185, 72, 78),
    "grey/blue": (100, 125, 142),
    "lemon lime": (191, 254, 40),
    "purple/pink": (215, 37, 222),
    "brown yellow": (178, 151, 5),
    "purple brown": (103, 58, 63),
    "wisteria": (168, 125, 194),
    "banana yellow": (250, 254, 75),
    "lipstick red": (192, 2, 47),
    "water blue": (14, 135, 204),
    "brown grey": (141, 132, 104),
    "vibrant purple": (173, 3, 222),
    "baby green": (140, 255, 158),
    "barf green": (148, 172, 2),
    "eggshell blue": (196, 255, 247),
    "sandy yellow": (253, 238, 115),
    "cool green": (51, 184, 100),
    "pale": (255, 249, 208),
    "blue/grey": (117, 141, 163),
    "hot magenta": (245, 4, 201),
    "greyblue": (119, 161, 181),
    "purpley": (135, 86, 228),
    "baby shit green": (136, 151, 23),
    "brownish pink": (194, 126, 121),
    "dark aquamarine": (1, 115, 113),
    "diarrhea": (159, 131, 3),
    "light mustard": (247, 213, 96),
    "pale sky blue": (189, 246, 254),
    "turtle green": (117, 184, 79),
    "bright olive": (156, 187, 4),
    "dark grey blue": (41, 70, 91),
    "greeny brown": (105, 96, 6),
    "lemon green": (173, 248, 2),
    "light periwinkle": (193, 198, 252),
    "seaweed green": (53, 173, 107),
    "sunshine yellow": (255, 253, 55),
    "ugly purple": (164, 66, 160),
    "medium pink": (243, 97, 150),
    "puke brown": (148, 119, 6),
    "very light pink": (255, 244, 242),
    "viridian": (30, 145, 103),
    "bile": (181, 195, 6),
    "faded yellow": (254, 255, 127),
    "very pale green": (207, 253, 188),
    "vibrant green": (10, 221, 8),
    "bright lime": (135, 253, 5),
    "spearmint": (30, 248, 118),
    "light aquamarine": (123, 253, 199),
    "light sage": (188, 236, 172),
    "yellowgreen": (187, 249, 15),
    "baby poo": (171, 144, 4),
    "dark seafoam": (31, 181, 122),
    "deep teal": (0, 85, 90),
    "heather": (164, 132, 172),
    "rust orange": (196, 85, 8),
    "dirty blue": (63, 130, 157),
    "fern green": (84, 141, 68),
    "bright lilac": (201, 94, 251),
    "weird green": (58, 229, 127),
    "peacock blue": (1, 103, 149),
    "avocado green": (135, 169, 34),
    "faded orange": (240, 148, 77),
    "grape purple": (93, 20, 81),
    "hot green": (37, 255, 41),
    "lime yellow": (208, 254, 29),
    "mango": (255, 166, 43),
    "shamrock": (1, 180, 76),
    "bubblegum": (255, 108, 181),
    "purplish brown": (107, 66, 71),
    "vomit yellow": (199, 193, 12),
    "pale cyan": (183, 255, 250),
    "key lime": (174, 255, 110),
    "tomato red": (236, 45, 1),
    "lightgreen": (118, 255, 123),
    "merlot": (115, 0, 57),
    "night blue": (4, 3, 72),
    "purpleish pink": (223, 78, 200),
    "apple": (110, 203, 60),
    "baby poop green": (143, 152, 5),
    "green apple": (94, 220, 31),
    "heliotrope": (217, 79, 245),
    "yellow/green": (200, 253, 61),
    "almost black": (7, 13, 13),
    "cool blue": (73, 132, 184),
    "leafy green": (81, 183, 59),
    "mustard brown": (172, 126, 4),
    "dusk": (78, 84, 129),
    "dull brown": (135, 110, 75),
    "frog green": (88, 188, 8),
    "vivid green": (47, 239, 16),
    "bright light green": (45, 254, 84),
    "fluro green": (10, 255, 2),
    "kiwi": (156, 239, 67),
    "seaweed": (24, 209, 123),
    "navy green": (53, 83, 10),
    "ultramarine blue": (24, 5, 219),
    "iris": (98, 88, 196),
    "pastel orange": (255, 150, 79),
    "yellowish orange": (255, 171, 15),
    "perrywinkle": (143, 140, 231),
    "tealish": (36, 188, 168),
    "dark plum": (63, 1, 44),
    "pear": (203, 248, 95),
    "pinkish orange": (255, 114, 76),
    "midnight purple": (40, 1, 55),
    "light urple": (179, 111, 246),
    "dark mint": (72, 192, 114),
    "greenish tan": (188, 203, 122),
    "light burgundy": (168, 65, 91),
    "turquoise blue": (6, 177, 196),
    "ugly pink": (205, 117, 132),
    "sandy": (241, 218, 122),
    "electric pink": (255, 4, 144),
    "muted purple": (128, 91, 135),
    "mid green": (80, 167, 71),
    "greyish": (168, 164, 149),
    "neon yellow": (207, 255, 4),
    "banana": (255, 255, 126),
    "carnation pink": (255, 127, 167),
    "tomato": (239, 64, 38),
    "sea": (60, 153, 146),
    "muddy brown": (136, 104, 6),
    "turquoise green": (4, 244, 137),
    "buff": (254, 246, 158),
    "fawn": (207, 175, 123),
    "muted blue": (59, 113, 159),
    "pale rose": (253, 193, 197),
    "dark mint green": (32, 192, 115),
    "amethyst": (155, 95, 192),
    "blue/green": (15, 155, 142),
    "chestnut": (116, 40, 2),
    "sick green": (157, 185, 44),
    "pea": (164, 191, 32),
    "rusty orange": (205, 89, 9),
    "stone": (173, 165, 135),
    "rose red": (190, 1, 60),
    "pale aqua": (184, 255, 235),
    "deep orange": (220, 77, 1),
    "earth": (162, 101, 62),
    "mossy green": (99, 139, 39),
    "grassy green": (65, 156, 3),
    "pale lime green": (177, 255, 101),
    "light grey blue": (157, 188, 212),
    "pale grey": (253, 253, 254),
    "asparagus": (119, 171, 86),
    "blueberry": (70, 65, 150),
    "purple red": (153, 1, 71),
    "pale lime": (190, 253, 115),
    "greenish teal": (50, 191, 132),
    "caramel": (175, 111, 9),
    "deep magenta": (160, 2, 92),
    "light peach": (255, 216, 177),
    "milk chocolate": (127, 78, 30),
    "ocher": (191, 155, 12),
    "off green": (107, 163, 83),
    "purply pink": (240, 117, 230),
    "lightblue": (123, 200, 246),
    "dusky blue": (71, 95, 148),
    "golden": (245, 191, 3),
    "light beige": (255, 254, 182),
    "butter yellow": (255, 253, 116),
    "dusky purple": (137, 91, 123),
    "french blue": (67, 107, 173),
    "ugly yellow": (208, 193, 1),
    "greeny yellow": (198, 248, 8),
    "orangish red": (244, 54, 5),
    "shamrock green": (2, 193, 77),
    "orangish brown": (178, 95, 3),
    "tree green": (42, 126, 25),
    "deep violet": (73, 6, 72),
    "gunmetal": (83, 98, 103),
    "blue/purple": (90, 6, 239),
    "cherry": (207, 2, 52),
    "sandy brown": (196, 166, 97),
    "warm grey": (151, 138, 132),
    "dark indigo": (31, 9, 84),
    "midnight": (3, 1, 45),
    "bluey green": (43, 177, 121),
    "grey pink": (195, 144, 155),
    "soft purple": (166, 111, 181),
    "blood": (119, 0, 1),
    "brown red": (146, 43, 5),
    "medium grey": (125, 127, 124),
    "berry": (153, 15, 75),
    "poo": (143, 115, 3),
    "purpley pink": (200, 60, 185),
    "light salmon": (254, 169, 147),
    "snot": (172, 187, 13),
    "easter purple": (192, 113, 254),
    "light yellow green": (204, 253, 127),
    "dark navy blue": (0, 2, 46),
    "drab": (130, 131, 68),
    "light rose": (255, 197, 203),
    "rouge": (171, 18, 57),
    "purplish red": (176, 5, 75),
    "slime green": (153, 204, 4),
    "baby poop": (147, 124, 0),
    "irish green": (1, 149, 41),
    "pink/purple": (239, 29, 231),
    "dark navy": (0, 4, 53),
    "greeny blue": (66, 179, 149),
    "light plum": (157, 87, 131),
    "pinkish grey": (200, 172, 169),
    "dirty orange": (200, 118, 6),
    "rust red": (170, 39, 4),
    "pale lilac": (228, 203, 255),
    "orangey red": (250, 66, 36),
    "primary blue": (8, 4, 249),
    "kermit green": (92, 178, 0),
    "brownish purple": (118, 66, 78),
    "murky green": (108, 122, 14),
    "wheat": (251, 221, 126),
    "very dark purple": (42, 1, 52),
    "bottle green": (4, 74, 5),
    "watermelon": (253, 70, 89),
    "deep sky blue": (13, 117, 248),
    "fire engine red": (254, 0, 2),
    "yellow ochre": (203, 157, 6),
    "pumpkin orange": (251, 125, 7),
    "pale olive": (185, 204, 129),
    "light lilac": (237, 200, 255),
    "lightish green": (97, 225, 96),
    "carolina blue": (138, 184, 254),
    "mulberry": (146, 10, 78),
    "shocking pink": (254, 2, 162),
    "auburn": (154, 48, 1),
    "bright lime green": (101, 254, 8),
    "celadon": (190, 253, 183),
    "pinkish brown": (177, 114, 97),
    "poo brown": (136, 95, 1),
    "bright sky blue": (2, 204, 254),
    "celery": (193, 253, 149),
    "dirt brown": (131, 101, 57),
    "strawberry": (251, 41, 67),
    "dark lime": (132, 183, 1),
    "copper": (182, 99, 37),
    "medium brown": (127, 81, 18),
    "muted green": (95, 160, 82),
    "robin's egg": (109, 237, 253),
    "bright aqua": (11, 249, 234),
    "bright lavender": (199, 96, 255),
    "ivory": (255, 255, 203),
    "very light purple": (246, 206, 252),
    "light navy": (21, 80, 132),
    "pink red": (245, 5, 79),
    "olive brown": (100, 84, 3),
    "poop brown": (122, 89, 1),
    "mustard green": (168, 181, 4),
    "ocean green": (61, 153, 115),
    "very dark blue": (0, 1, 51),
    "dusty green": (118, 169, 115),
    "light navy blue": (46, 90, 136),
    "minty green": (11, 247, 125),
    "adobe": (189, 108, 72),
    "barney": (172, 29, 184),
    "jade green": (43, 175, 106),
    "bright light blue": (38, 247, 253),
    "light lime": (174, 253, 108),
    "dark khaki": (155, 143, 85),
    "orange yellow": (255, 173, 1),
    "ocre": (198, 156, 4),
    "maize": (244, 208, 84),
    "faded pink": (222, 157, 172),
    "british racing green": (5, 72, 13),
    "sandstone": (201, 174, 116),
    "mud brown": (96, 70, 15),
    "light sea green": (152, 246, 176),
    "robin egg blue": (138, 241, 254),
    "aqua marine": (46, 232, 187),
    "dark sea green": (17, 135, 93),
    "soft pink": (253, 176, 192),
    "orangey brown": (177, 96, 2),
    "cherry red": (247, 2, 42),
    "burnt yellow": (213, 171, 9),
    "brownish grey": (134, 119, 95),
    "camel": (198, 159, 89),
    "purplish grey": (122, 104, 127),
    "marine": (4, 46, 96),
    "greyish pink": (200, 141, 148),
    "pale turquoise": (165, 251, 213),
    "pastel yellow": (255, 254, 113),
    "bluey purple": (98, 65, 199),
    "canary yellow": (255, 254, 64),
    "faded red": (211, 73, 78),
    "sepia": (152, 94, 43),
    "coffee": (166, 129, 76),
    "bright magenta": (255, 8, 232),
    "mocha": (157, 118, 81),
    "ecru": (254, 255, 202),
    "purpleish": (152, 86, 141),
    "cranberry": (158, 0, 58),
    "darkish green": (40, 124, 55),
    "brown orange": (185, 105, 2),
    "dusky rose": (186, 104, 115),
    "melon": (255, 120, 85),
    "sickly green": (148, 178, 28),
    "silver": (197, 201, 199),
    "purply blue": (102, 26, 238),
    "purpleish blue": (97, 64, 239),
    "hospital green": (155, 229, 170),
    "shit brown": (123, 88, 4),
    "mid blue": (39, 106, 179),
    "amber": (254, 179, 8),
    "easter green": (140, 253, 126),
    "soft blue": (100, 136, 234),
    "cerulean blue": (5, 110, 238),
    "golden brown": (178, 122, 1),
    "bright turquoise": (15, 254, 249),
    "red pink": (250, 42, 85),
    "red purple": (130, 7, 71),
    "greyish brown": (122, 106, 79),
    "vermillion": (244, 50, 12),
    "russet": (161, 57, 5),
    "steel grey": (111, 130, 138),
    "lighter purple": (165, 90, 244),
    "bright violet": (173, 10, 253),
    "prussian blue": (0, 69, 119),
    "slate green": (101, 141, 109),
    "dirty pink": (202, 123, 128),
    "dark blue green": (0, 82, 73),
    "pine": (43, 93, 52),
    "yellowy green": (191, 241, 40),
    "dark gold": (181, 148, 16),
    "bluish": (41, 118, 187),
    "darkish blue": (1, 65, 130),
    "dull red": (187, 63, 63),
    "pinky red": (252, 38, 71),
    "bronze": (168, 121, 0),
    "pale teal": (130, 203, 178),
    "military green": (102, 124, 62),
    "barbie pink": (254, 70, 165),
    "bubblegum pink": (254, 131, 204),
    "pea soup green": (148, 166, 23),
    "dark mustard": (168, 137, 5),
    "shit": (127, 95, 0),
    "medium purple": (158, 67, 162),
    "very dark green": (6, 46, 3),
    "dirt": (138, 110, 69),
    "dusky pink": (204, 122, 139),
    "red violet": (158, 1, 104),
    "lemon yellow": (253, 255, 56),
    "pistachio": (192, 250, 139),
    "dull yellow": (238, 220, 91),
    "dark lime green": (126, 189, 1),
    "denim blue": (59, 91, 146),
    "teal blue": (1, 136, 159),
    "lightish blue": (61, 122, 253),
    "purpley blue": (95, 52, 231),
    "light indigo": (109, 90, 207),
    "swamp green": (116, 133, 0),
    "brown green": (112, 108, 17),
    "dark maroon": (60, 0, 8),
    "hot purple": (203, 0, 245),
    "dark forest green": (0, 45, 4),
    "faded blue": (101, 140, 187),
    "drab green": (116, 149, 81),
    "light lime green": (185, 255, 102),
    "snot green": (157, 193, 0),
    "yellowish": (250, 238, 102),
    "light blue green": (126, 251, 179),
    "bordeaux": (123, 0, 44),
    "light mauve": (194, 146, 161),
    "ocean": (1, 123, 146),
    "marigold": (252, 192, 6),
    "muddy green": (101, 116, 50),
    "dull orange": (216, 134, 59),
    "steel": (115, 133, 149),
    "electric purple": (170, 35, 255),
    "fluorescent green": (8, 255, 8),
    "yellowish brown": (155, 122, 1),
    "blush": (242, 158, 142),
    "soft green": (111, 194, 118),
    "bright orange": (255, 91, 0),
    "lemon": (253, 255, 82),
    "purple grey": (134, 111, 133),
    "acid green": (143, 254, 9),
    "pale lavender": (238, 207, 254),
    "violet blue": (81, 10, 201),
    "light forest green": (79, 145, 83),
    "burnt red": (159, 35, 5),
    "khaki green": (114, 134, 57),
    "cerise": (222, 12, 98),
    "faded purple": (145, 110, 153),
    "apricot": (255, 177, 109),
    "dark olive green": (60, 77, 3),
    "grey brown": (127, 112, 83),
    "green grey": (119, 146, 111),
    "true blue": (1, 15, 204),
    "pale violet": (206, 174, 250),
    "periwinkle blue": (143, 153, 251),
    "light sky blue": (198, 252, 255),
    "blurple": (85, 57, 204),
    "green brown": (84, 78, 3),
    "bluegreen": (1, 122, 121),
    "bright teal": (1, 249, 198),
    "brownish yellow": (201, 176, 3),
    "pea soup": (146, 153, 1),
    "forest": (11, 85, 9),
    "barney purple": (160, 4, 152),
    "ultramarine": (32, 0, 177),
    "purplish": (148, 86, 140),
    "puke yellow": (194, 190, 14),
    "bluish grey": (116, 139, 151),
    "dark periwinkle": (102, 95, 209),
    "dark lilac": (156, 109, 165),
    "reddish": (196, 66, 64),
    "light maroon": (162, 72, 87),
    "dusty purple": (130, 95, 135),
    "terra cotta": (201, 100, 59),
    "avocado": (144, 177, 52),
    "marine blue": (1, 56, 106),
    "teal green": (37, 163, 111),
    "slate grey": (89, 101, 109),
    "lighter green": (117, 253, 99),
    "electric green": (33, 252, 13),
    "dusty blue": (90, 134, 173),
    "golden yellow": (254, 198, 21),
    "bright yellow": (255, 253, 1),
    "light lavender": (223, 197, 254),
    "umber": (178, 100, 0),
    "poop": (127, 94, 0),
    "dark peach": (222, 126, 93),
    "jungle green": (4, 130, 67),
    "eggshell": (255, 255, 212),
    "denim": (59, 99, 140),
    "yellow brown": (183, 148, 0),
    "dull purple": (132, 89, 126),
    "chocolate brown": (65, 25, 0),
    "wine red": (123, 3, 35),
    "neon blue": (4, 217, 255),
    "dirty green": (102, 126, 44),
    "light tan": (251, 238, 172),
    "ice blue": (215, 255, 254),
    "cadet blue": (78, 116, 150),
    "dark mauve": (135, 76, 98),
    "very light blue": (213, 255, 255),
    "grey purple": (130, 109, 140),
    "pastel pink": (255, 186, 205),
    "very light green": (209, 255, 189),
    "dark sky blue": (68, 142, 228),
    "evergreen": (5, 71, 42),
    "dull pink": (213, 134, 157),
    "aubergine": (61, 7, 52),
    "mahogany": (74, 1, 0),
    "reddish orange": (248, 72, 28),
    "deep green": (2, 89, 15),
    "vomit green": (137, 162, 3),
    "purple pink": (224, 63, 216),
    "dusty pink": (213, 138, 148),
    "faded green": (123, 178, 116),
    "camo green": (82, 101, 37),
    "pinky purple": (201, 76, 190),
    "pink purple": (219, 75, 218),
    "brownish red": (158, 54, 35),
    "dark rose": (181, 72, 93),
    "mud": (115, 92, 18),
    "brownish": (156, 109, 87),
    "emerald green": (2, 143, 30),
    "pale brown": (177, 145, 110),
    "dull blue": (73, 117, 156),
    "burnt umber": (160, 69, 14),
    "medium green": (57, 173, 72),
    "clay": (182, 106, 80),
    "light aqua": (140, 255, 219),
    "light olive green": (164, 190, 92),
    "brownish orange": (203, 119, 35),
    "dark aqua": (5, 105, 107),
    "purplish pink": (206, 93, 174),
    "dark salmon": (200, 90, 83),
    "greenish grey": (150, 174, 141),
    "jade": (31, 167, 116),
    "ugly green": (122, 151, 3),
    "dark beige": (172, 147, 98),
    "emerald": (1, 160, 73),
    "pale red": (217, 84, 77),
    "light magenta": (250, 95, 247),
    "sky": (130, 202, 252),
    "light cyan": (172, 255, 252),
    "yellow orange": (252, 176, 1),
    "reddish purple": (145, 9, 81),
    "reddish pink": (254, 44, 84),
    "orchid": (200, 117, 196),
    "dirty yellow": (205, 197, 10),
    "orange red": (253, 65, 30),
    "deep red": (154, 2, 0),
    "orange brown": (190, 100, 0),
    "cobalt blue": (3, 10, 167),
    "neon pink": (254, 1, 154),
    "rose pink": (247, 135, 154),
    "greyish purple": (136, 113, 145),
    "raspberry": (176, 1, 73),
    "aqua green": (18, 225, 147),
    "salmon pink": (254, 123, 124),
    "tangerine": (255, 148, 8),
    "brownish green": (106, 110, 9),
    "red brown": (139, 46, 22),
    "greenish brown": (105, 97, 18),
    "pumpkin": (225, 119, 1),
    "pine green": (10, 72, 30),
    "charcoal": (52, 56, 55),
    "baby pink": (255, 183, 206),
    "cornflower": (106, 121, 247),
    "blue violet": (93, 6, 233),
    "chocolate": (61, 28, 2),
    "greyish green": (130, 166, 125),
    "scarlet": (190, 1, 25),
    "green yellow": (201, 255, 39),
    "dark olive": (55, 62, 2),
    "sienna": (169, 86, 30),
    "pastel purple": (202, 160, 255),
    "terracotta": (202, 102, 65),
    "aqua blue": (2, 216, 233),
    "sage green": (136, 179, 120),
    "blood red": (152, 0, 2),
    "deep pink": (203, 1, 98),
    "grass": (92, 172, 45),
    "moss": (118, 153, 88),
    "pastel blue": (162, 191, 254),
    "bluish green": (16, 166, 116),
    "green blue": (6, 180, 139),
    "dark tan": (175, 136, 74),
    "greenish blue": (11, 139, 135),
    "pale orange": (255, 167, 86),
    "vomit": (162, 164, 21),
    "forrest green": (21, 68, 6),
    "dark lavender": (133, 103, 152),
    "dark violet": (52, 1, 63),
    "purple blue": (99, 45, 233),
    "dark cyan": (10, 136, 138),
    "olive drab": (111, 118, 50),
    "pinkish": (212, 106, 126),
    "cobalt": (30, 72, 143),
    "neon purple": (188, 19, 254),
    "light turquoise": (126, 244, 204),
    "apple green": (118, 205, 38),
    "dull green": (116, 166, 98),
    "wine": (128, 1, 63),
    "powder blue": (177, 209, 252),
    "off white": (255, 255, 228),
    "electric blue": (6, 82, 255),
    "dark turquoise": (4, 92, 90),
    "blue purple": (87, 41, 206),
    "azure": (6, 154, 243),
    "bright red": (255, 0, 13),
    "pinkish red": (241, 12, 69),
    "cornflower blue": (81, 112, 215),
    "light olive": (172, 191, 105),
    "grape": (108, 52, 97),
    "greyish blue": (94, 129, 157),
    "purplish blue": (96, 30, 249),
    "yellowish green": (176, 221, 22),
    "greenish yellow": (205, 253, 2),
    "medium blue": (44, 111, 187),
    "dusty rose": (192, 115, 122),
    "light violet": (214, 180, 252),
    "midnight blue": (2, 0, 53),
    "bluish purple": (112, 59, 231),
    "red orange": (253, 60, 6),
    "dark magenta": (150, 0, 86),
    "greenish": (64, 163, 104),
    "ocean blue": (3, 113, 156),
    "coral": (252, 90, 80),
    "cream": (255, 255, 194),
    "reddish brown": (127, 43, 10),
    "burnt sienna": (176, 78, 15),
    "brick": (160, 54, 35),
    "sage": (135, 174, 115),
    "grey green": (120, 155, 115),
    "white": (255, 255, 255),
    "robin's egg blue": (152, 239, 249),
    "moss green": (101, 139, 56),
    "steel blue": (90, 125, 154),
    "eggplant": (56, 8, 53),
    "light yellow": (255, 254, 122),
    "leaf green": (92, 169, 4),
    "light grey": (216, 220, 214),
    "puke": (165, 165, 2),
    "pinkish purple": (214, 72, 215),
    "sea blue": (4, 116, 149),
    "pale purple": (183, 144, 212),
    "slate blue": (91, 124, 153),
    "blue grey": (96, 124, 142),
    "hunter green": (11, 64, 8),
    "fuchsia": (237, 13, 217),
    "crimson": (140, 0, 15),
    "pale yellow": (255, 255, 132),
    "ochre": (191, 144, 5),
    "mustard yellow": (210, 189, 10),
    "light red": (255, 71, 76),
    "cerulean": (4, 133, 209),
    "pale pink": (255, 207, 220),
    "deep blue": (4, 2, 115),
    "rust": (168, 60, 9),
    "light teal": (144, 228, 193),
    "slate": (81, 101, 114),
    "goldenrod": (250, 194, 5),
    "dark yellow": (213, 182, 10),
    "dark grey": (54, 55, 55),
    "army green": (75, 93, 22),
    "grey blue": (107, 139, 164),
    "seafoam": (128, 249, 173),
    "puce": (165, 126, 82),
    "spring green": (169, 249, 113),
    "dark orange": (198, 81, 2),
    "sand": (226, 202, 118),
    "pastel green": (176, 255, 157),
    "mint": (159, 254, 176),
    "light orange": (253, 170, 72),
    "bright pink": (254, 1, 177),
    "chartreuse": (193, 248, 10),
    "deep purple": (54, 1, 63),
    "dark brown": (52, 28, 2),
    "taupe": (185, 162, 129),
    "pea green": (142, 171, 18),
    "puke green": (154, 174, 7),
    "kelly green": (2, 171, 46),
    "seafoam green": (122, 249, 171),
    "blue green": (19, 126, 109),
    "khaki": (170, 166, 98),
    "burgundy": (97, 0, 35),
    "dark teal": (1, 77, 78),
    "brick red": (143, 20, 2),
    "royal purple": (75, 0, 110),
    "plum": (88, 15, 65),
    "mint green": (143, 255, 159),
    "gold": (219, 180, 12),
    "baby blue": (162, 207, 254),
    "yellow green": (192, 251, 45),
    "bright purple": (190, 3, 253),
    "dark red": (132, 0, 0),
    "pale blue": (208, 254, 254),
    "grass green": (63, 155, 11),
    "navy": (1, 21, 62),
    "aquamarine": (4, 216, 178),
    "burnt orange": (192, 78, 1),
    "neon green": (12, 255, 12),
    "bright blue": (1, 101, 252),
    "rose": (207, 98, 117),
    "light pink": (255, 209, 223),
    "mustard": (206, 179, 1),
    "indigo": (56, 2, 130),
    "lime": (170, 255, 50),
    "sea green": (83, 252, 161),
    "periwinkle": (142, 130, 254),
    "dark pink": (203, 65, 107),
    "olive green": (103, 122, 4),
    "peach": (255, 176, 124),
    "pale green": (199, 253, 181),
    "light brown": (173, 129, 80),
    "hot pink": (255, 2, 141),
    "black": (0, 0, 0),
    "lilac": (206, 162, 253),
    "navy blue": (0, 17, 70),
    "royal blue": (5, 4, 170),
    "beige": (230, 218, 166),
    "salmon": (255, 121, 108),
    "olive": (110, 117, 14),
    "maroon": (101, 0, 33),
    "bright green": (1, 255, 7),
    "dark purple": (53, 6, 62),
    "mauve": (174, 113, 129),
    "forest green": (6, 71, 12),
    "aqua": (19, 234, 201),
    "cyan": (0, 255, 255),
    "tan": (209, 178, 111),
    "dark blue": (0, 3, 91),
    "lavender": (199, 159, 239),
    "turquoise": (6, 194, 172),
    "dark green": (3, 53, 0),
    "violet": (154, 14, 234),
    "light purple": (191, 119, 246),
    "lime green": (137, 254, 5),
    "grey": (146, 149, 145),
    "sky blue": (117, 187, 253),
    "yellow": (255, 255, 20),
    "magenta": (194, 0, 120),
    "light green": (150, 249, 123),
    "orange": (249, 115, 6),
    "teal": (2, 147, 134),
    "light blue": (149, 208, 252),
    "red": (229, 0, 0),
    "brown": (101, 55, 0),
    "pink": (255, 129, 192),
    "blue": (3, 67, 223),
    "green": (21, 176, 26),
    "purple": (126, 30, 156),
}


def get_delta_e(rgba, rgbb, upscaled=False):
    """Get color difference according to CIE2000, if upscaled the range is 0-255, else between 0 and 1"""
    color1_rgb = sRGBColor(rgba[0], rgba[1], rgba[2], is_upscaled=upscaled)
    color2_rgb = sRGBColor(rgbb[0], rgbb[1], rgbb[2], is_upscaled=upscaled)

    # Convert from RGB to Lab Color Space
    color1_lab = convert_color(color1_rgb, LabColor)

    # Convert from RGB to Lab Color Space
    color2_lab = convert_color(color2_rgb, LabColor)

    # Find the color difference
    delta_e = delta_e_cie2000(color1_lab, color2_lab)

    return delta_e


def closest_name(requested_colour):
    """Return the perceptually closest color name from the xkcd survey given and RGB tuple in the range 0-255"""
    min_colours = {}
    for name, rgb in XKCD_RGB_DICT.items():
        distance = get_delta_e(rgb, requested_colour, upscaled=True)
        min_colours[distance] = name
    return min_colours[min(min_colours.keys())]


def pil_to_array(pil):
    return np.asarray(pil)


def array_to_pil(array):
    return Image.fromarray(array)


def calibrate_image(
    image, card, excluded=None, algorithm="finlayson", only_white_point=True
):  # pylint:disable=too-many-locals, too-many-arguments
    """Use colour to automatically calibrate the image"""
    if card == "spyder24":
        reference = TARGET_SPYDER24
    else:
        raise NotImplementedError

    linear_image = colour.cctf_decoding(image)  # decode to linear RGB

    try:
        swatches = detect_colour_checkers_segmentation(linear_image)[0][
            ::-1
        ]  # black first

        # neutralization (white balance) based on # 3E
        im = linear_image / swatches[3]  # pylint:disable=invalid-name
        im *= colour.cctf_decoding(reference[3])  # pylint:disable=invalid-name

        del linear_image
        del swatches

        if not only_white_point:
            swatches_wb = detect_colour_checkers_segmentation(im)[
                0
            ]  # [::-1]  # black first
            if algorithm == "finlayson":
                algorithm_ = "Finlayson 2015"
            elif algorithm == "cheung":
                algorithm_ = "Cheung 2004"
            elif algorithm == "vandermonde":
                algorithm_ = "Vandermonde"
            else:
                # log this case
                algorithm_ = "Finlayson 2015"

            if isinstance(excluded, list):
                swatches_wb = np.delete(swatches_wb, excluded, axis=0)
                reference = np.delete(reference, excluded, axis=0)

            im_cal_linear = colour.colour_correction(
                im, swatches_wb, colour.cctf_decoding(reference), method=algorithm_
            )

            im_cal_non_linear = colour.cctf_encoding(im_cal_linear)
            del im_cal_linear
            im_pil = Image.fromarray(
                (np.clip(im_cal_non_linear, 0, 1) * 255).astype(np.uint8)
            )
        else:
            im = colour.cctf_encoding(im)
            im_cal_non_linear = im
            im_pil = Image.fromarray((np.clip(im, 0, 1) * 255).astype(np.uint8))

        try:
            swatches_calibrated = detect_colour_checkers_segmentation(
                im_cal_non_linear
            )[0][::-1]
            del im_cal_non_linear
            label = np.arange(0, len(swatches_wb))
            target_matrix = np.zeros((len(label), 4))
            measured_matrix = np.zeros((len(label), 4))
            del swatches_wb

            target_matrix[:, 0] = label
            measured_matrix[:, 0] = label

            measured_matrix[:, 1:] = swatches_calibrated
            target_matrix[:, 1:] = reference

            df_sm = pd.DataFrame(measured_matrix, columns=["label", "r", "g", "b"])
            df_tm = pd.DataFrame(target_matrix, columns=["label", "r", "g", "b"])

            merged_df = pd.merge(
                df_sm,
                df_tm,
                left_on="label",
                right_on="label",
                suffixes=("_source", "_target"),
            )
            merged_df["label"] = merged_df["label"]
        except Exception as e:
            merged_df = pd.DataFrame(
                [[np.nan] * 7],
                columns=[
                    "label",
                    "r_source",
                    "g_source",
                    "b_source",
                    "r_target",
                    "g_target",
                    "b_target",
                ],
            )

        return im_pil, merged_df
    except Exception as e:  # pylint:disable=invalid-name
        raise ValueError(e)


def plot_parity(merged_df):
    """Make a partiy plot indicating the quality of the calibration"""
    fig = make_subplots(rows=1, cols=3)

    fig.add_trace(
        go.Scatter(
            x=merged_df["r_source"],
            y=merged_df["r_target"],
            hovertext=merged_df["label"],
            mode="markers",
            marker={"color": "red"},
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=merged_df["g_source"],
            y=merged_df["g_target"],
            hovertext=merged_df["label"],
            mode="markers",
            marker={"color": "green"},
        ),
        row=1,
        col=2,
    )

    fig.add_trace(
        go.Scatter(
            x=merged_df["b_source"],
            y=merged_df["b_target"],
            hovertext=merged_df["label"],
            mode="markers",
            marker={"color": "blue"},
        ),
        row=1,
        col=3,
    )

    fig.update_layout(showlegend=False)
    fig["layout"].update(margin=dict(l=0, r=0, b=0, t=0))

    return fig


def get_average_color(x, y, image):  # pylint:disable=too-many-locals, invalid-name
    """Returns a 3-tuple containing the RGB value of the average color of the
    given square bounded area of length = n whose origin (top left corner)
    is (x, y) in the given image"""
    logger.debug("Getting average color of %s", image)
    height = image.size[1]

    lower, upper = list(map(int, y))
    left, right = list(map(int, x))
    # Adjust height difference

    upper = height - upper
    lower = height - lower

    x_0 = min([left, right])
    x_1 = max([left, right])

    y_0 = min([lower, upper])
    y_1 = max([lower, upper])

    # ugly because numpy somehow flips the axis
    reds = []
    greens = []
    blues = []
    data = []
    for i in range(x_0, x_1):
        for j in range(y_0, y_1):
            red, green, blue = image.getpixel((i, j))
            reds.append(red)
            greens.append(green)
            blues.append(blue)
            data.append({"R": red, "G": green, "B": blue})

    return (
        (
            np.mean(reds),
            np.mean(greens),
            np.mean(blues),
            np.std(reds),
            np.std(greens),
            np.std(blues),
        ),
        data,
    )


def rotate_image(image):
    return image.rotate(90)


def flip_image(image):
    return ImageOps.flip(image)


def mirror_image(image):
    return ImageOps.mirror(image)
