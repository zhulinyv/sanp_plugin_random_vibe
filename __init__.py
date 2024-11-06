import random
from pathlib import Path

import gradio as gr

from src.text2image_nsfw import prepare_input as t2i_input
from src.text2image_sfw import prepare_input as batchtxt_input
from utils.env import env
from utils.imgtools import img_to_base64
from utils.jsondata import json_for_vibe
from utils.prepare import logger
from utils.utils import (
    file_path2list,
    generate_image,
    open_folder,
    read_json,
    save_image,
    sleep_for_cool,
)

webui_language = read_json(f"./files/languages/{env.webui_lang}/webui.json")


def gen_script(script_type, *args):
    with open("stand_alone_scripts.py", "w", encoding="utf-8") as script:
        if script_type == "vibe":
            script.write(
                """from plugins.t2i.sanp_plugin_random_vibe import vibe
while 1:
    vibe({}, r"{}")
""".format(
                    args[0], args[1]
                )
            )
        else:
            ...
    logger.success("生成成功, 运行 run_stand_alone_scripts.bat 即可独立执行该操作")


def open_output_folder_block(output_folder):
    open_output_folder_folder = gr.Button(webui_language["t2i"]["open_folder"], scale=1)
    open_output_folder_folder.click(
        open_folder, inputs=gr.Textbox(Path(f"./output/{output_folder}"), visible=False)
    )


def prepare_json(input_, sm, scale, negative, input_imgs):
    json_for_vibe["input"] = input_
    if isinstance(env.img_size, int):
        resolution_list = [[832, 1216], [1024, 1024], [1216, 832]]
        resolution = random.choice(resolution_list)
    elif isinstance(env.img_size, list):
        resolution = env.img_size
    json_for_vibe["parameters"]["width"] = resolution[0]
    json_for_vibe["parameters"]["height"] = resolution[1]
    json_for_vibe["parameters"]["scale"] = env.scale if scale == 0 else scale
    json_for_vibe["parameters"]["sampler"] = env.sampler
    json_for_vibe["parameters"]["steps"] = env.steps
    json_for_vibe["parameters"]["sm"] = env.sm if sm == 0 else True
    json_for_vibe["parameters"]["sm_dyn"] = (
        env.sm_dyn if (env.sm or (sm == 1)) and env.sm_dyn else False
    )
    json_for_vibe["parameters"]["skip_cfg_above_sigma"] = (
        19.343056794463642 if env.variety else None
    )
    json_for_vibe["parameters"]["dynamic_thresholding"] = env.decrisp
    json_for_vibe["parameters"]["noise_schedule"] = env.noise_schedule
    seed = random.randint(1000000000, 9999999999) if env.seed == -1 else env.seed
    json_for_vibe["parameters"]["seed"] = seed
    json_for_vibe["parameters"]["negative_prompt"] = negative

    json_for_vibe["parameters"]["add_original_image"] = True

    reference_image_multiple = []
    reference_information_extracted_multiple = []
    reference_strength_multiple = []
    img_list = file_path2list(Path(input_imgs))
    for img in img_list:
        reference_image_multiple.append(img_to_base64(Path(input_imgs) / img))
        reference_list = img.replace(".png", "").replace(".jpg", "").split("_")
        reference_information_extracted_multiple.append(float(reference_list[1]))
        reference_strength_multiple.append(float(reference_list[2]))

    logger.debug(
        f"""
基底图片: {img_list}
信息提取: {reference_information_extracted_multiple}
参考强度: {reference_strength_multiple}"""
    )

    json_for_vibe["parameters"]["reference_image_multiple"] = reference_image_multiple
    json_for_vibe["parameters"][
        "reference_information_extracted_multiple"
    ] = reference_information_extracted_multiple
    json_for_vibe["parameters"][
        "reference_strength_multiple"
    ] = reference_strength_multiple

    return json_for_vibe, seed


def vibe(blue_imgs: bool, input_imgs):
    if blue_imgs:
        prompt = t2i_input(
            "随机",
            "随机",
            "随机",
            "随机",
            "随机",
            "随机",
            "随机",
            "随机",
            "随机",
            "随机",
        )[0]
    else:
        file, prompt = batchtxt_input("", "最前面(Top)", False, False, False)
        sm = env.sm
        scale = env.scale
        data = read_json("./files/favorite.json")
        negative = random.choice(data["negative_prompt"]["belief"])
        choose_game = choose_character = "None"
    json_for_vibe, seed = prepare_json(prompt, sm, scale, negative, input_imgs)
    saved_path = save_image(
        generate_image(json_for_vibe), "vibe", seed, choose_game, choose_character
    )
    sleep_for_cool(env.t2i_cool_time - 3, env.t2i_cool_time + 3)

    return saved_path, saved_path


def plugin():
    with gr.Tab("随机Vibe"):
        with gr.Row():
            with gr.Column(scale=5):
                gr.Markdown(webui_language["t2i"]["description"])
            with gr.Column(scale=1):
                open_output_folder_block("vibe")
                generate_vibe_transfer_script_button = gr.Button(
                    webui_language["t2i"]["script_gen"]
                )
        with gr.Column():
            with gr.Row():
                vibe_transfer_generate_forever_button = gr.Button(
                    webui_language["random blue picture"]["generate_forever"],
                    scale=1,
                )
                vibe_transfer_stop_button = gr.Button(
                    webui_language["random blue picture"]["stop_button"], scale=1
                )
                vibe_transfer_nsfw_switch = gr.Checkbox(
                    False, label=webui_language["vibe"]["blue_imgs"]
                )
            vibe_transfer_input_images = gr.Textbox(
                "", label=webui_language["vibe"]["input_imgs"]
            )
            vibe_transfer_output_image = gr.Image(scale=2)
            _vibe_transfer_output_image = gr.Image(visible=False)
        vibe_transfer_cancel_event = _vibe_transfer_output_image.change(
            fn=vibe,
            inputs=[vibe_transfer_nsfw_switch, vibe_transfer_input_images],
            outputs=[vibe_transfer_output_image, _vibe_transfer_output_image],
            show_progress="hidden",
        )
        vibe_transfer_generate_forever_button.click(
            fn=vibe,
            inputs=[vibe_transfer_nsfw_switch, vibe_transfer_input_images],
            outputs=[vibe_transfer_output_image, _vibe_transfer_output_image],
        )
        vibe_transfer_stop_button.click(
            None, None, None, cancels=[vibe_transfer_cancel_event]
        )
        generate_vibe_transfer_script_button.click(
            gen_script,
            inputs=[
                gr.Textbox("vibe", visible=False),
                vibe_transfer_nsfw_switch,
                vibe_transfer_input_images,
            ],
            outputs=None,
        )
