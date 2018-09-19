#!/usr/bin/python3
"""Provide functions for creation of images and animations featuring text."""

from PIL import Image, ImageDraw, ImageFont
from os import environ
import subprocess
from math import floor, log, ceil
from functools import wraps
from text_img_creator.img_utils import ImageProps


fname_key = ImageProps.fname_key
ext_key = ImageProps.ext_key
width_key = ImageProps.width_key
height_key = ImageProps.height_key
back_col_key = ImageProps.back_col_key
frame_fname_base = "frame_"
default_color_mode = "RGBA"
black_col = (0, 0, 0, 255)
white_col = (255, 255, 255, 255)
transparent_col = (0, 0, 0, 0)


def get_bash_var_name(*args):
    """Create variable name of an ImageProp object."""
    f, e, k = args
    if e.startswith("."):
        e = e[1:]

    ret = "img_"
    for arg in [f, e, k]:
        if arg:
            ret += arg + "_"

    ret = ret.strip("_")
    return ret


def record_image_properties(func):
    """Write ImageProp (or dict) properties to file."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        properties = func(*args, **kwargs)
        with open(environ["img_properties"]) as ip:
            lines = ip.readlines()
        bash_vars = {}
        for p in properties:
            f = p[fname_key]
            e = p[ext_key]
            for k, v in p.items():
                if k == ext_key:
                    bash_vars[get_bash_var_name(f, e, "")] = str(f) + str(v)
                bash_vars[get_bash_var_name(f, e, k)] = str(v)

        for i in range(len(lines)):
            if lines[i].startswith("export"):
                split_line = lines[i].split()
                var, val = split_line[1].split("=")
                if var in bash_vars:
                    val = bash_vars[var]
                    del bash_vars[var]
                    bash_c = ["export", var + "=" + '"' + val + '"']
                    lines[i] = " ".join(bash_c) + "\n"

        for k, v in bash_vars.items():
            lines.append(" ".join(["export", k + "=" + '"' + v + '"']) + "\n")

        with open(environ["img_properties"], "w+") as ip:
            ip.writelines(lines)

        return properties

    return wrapper


def decode_hex_col(color):
    """Translate hex col into 3 tuple col."""
    if color.startswith("#"):
        color = color[1:]
    return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))


def encode_hex_col(color):
    """Translate 3 tuple char into hex col."""
    hex_col = "#"
    if isinstance(color, tuple):
        for c in color:
            hex_col += format(c, '02x')
            return hex_col
    return color


def determine_min_image_size(
    text,
    text_seperation,
    font_name=None,
    font_size=None,
    horizontal=False
):
    """Determine minimum image size to contain text."""
    def generate_fonts():
        i = 0
        while True:
            yield ImageFont.truetype(font_name, i)
            i += 1

    def image_size_with_font(t, f):
            tw, th = tmp_draw.textsize(t, font=f)
            small_img = Image.new(default_color_mode, (tw, th), transparent_col)
            small_draw = ImageDraw.Draw(small_img)
            small_draw.text((0, 0), t, font=f, fill=text_fill_col)

            # Find actual text width

            # Find Fatty height
            pixels = small_img.load()
            top_till_text = 0
            bottom_till_text = th
            found_top = False
            found_bottom = False
            for y in range(th):
                for x in range(tw):
                    if pixels[x, y] == text_fill_col and (not found_top):
                        top_till_text = y
                        found_top = True
                        if found_bottom:
                            break

                    if pixels[x, (th - 1) - y] == text_fill_col and (not found_bottom):
                        bottom_till_text = (th - 1) - y
                        found_bottom = True
                        if found_top:
                            break
                else:
                    continue
                break

            # Find Fatty Width
            widest_left_x = tw
            widest_right_x = 0
            found_left_x = False
            found_right_x = False
            for x in range(tw):
                for y in range(th):
                    if pixels[x, y] == text_fill_col and (not found_left_x):
                        widest_left_x = x
                        found_left_x = True
                        if found_right_x:
                            break
                    if pixels[(tw - 1) - x, y] == text_fill_col and (not found_right_x):
                        widest_right_x = (tw - 1) - x
                        found_right_x = True
                        if found_left_x:
                            break
                else:
                    continue
                break

            width = widest_right_x - widest_left_x
            height = bottom_till_text - top_till_text
            start_x = -widest_left_x
            start_y = -top_till_text

            return width, height, start_x, start_y

    width = height = 1000
    tmp = Image.new(default_color_mode, (width, height), transparent_col)
    tmp_draw = ImageDraw.Draw(tmp)
    tps = []
    min_width = min_height = 0
    text_fill_col = white_col
    # Iterate through text set
    render_font = None
    for t in text:

        # Set target_width or target_height based on text
        target_width = t.target_width
        target_height = t.target_height
        p_t, p_b, p_l, p_r = t.padding
        str_text = str(t)
        if font_size is None:
            fonts = generate_fonts()
        else:
            fonts = [ImageFont.truetype(font_name, font_size)]

        # Calibrate font such that target width or height are met (or undermet)
        for f in fonts:
            try:
                if f.size > render_font.size:
                    break
            except AttributeError:
                pass

            w, h, sx, sy = image_size_with_font(str_text, f)

            w += p_l + p_r
            h += p_t + p_b
            sx += p_l
            sy += p_t
            if target_height:
                if h > target_height:
                    break
            if target_width:
                if w > target_width:
                    break

            t_width = w
            t_height = h
            t_start_x = sx
            t_start_y = sy

        # Set render font to lowest value so far
        render_font = f if render_font is None else render_font
        if f.size < render_font.size:
            render_font = f.size

        # Set text height and width to targets (if exists)
        if target_height:
            t_height = target_height
        if target_width:
            t_width = target_width

        t.width = t_width
        t.height = t_height
        t.sx = t_start_x
        t.sy = t_start_y
        tps.append(t)

        # Add text seperation based on image orientation
        if horizontal:
            if t.height > min_height:
                min_height = t.height
            min_width += t.width + text_seperation(t.width)
        else:
            if t.width > min_width:
                min_width = t.width
            min_height += t.height + text_seperation(t.height)

    # strip trailing seperation
    if horizontal:
        min_width -= text_seperation(t_width)
    else:
        min_height -= text_seperation(t_height)

    return min_width, min_height, tps, render_font


def strip_px(s):
    """Remove px from size definition."""
    px = "px"
    if s.endswith(px):
        s = s[:-len(px)]
    return s


def create_image(
    width,
    height,
    col,
    mode=default_color_mode,
    fname="tmp",
    ext=None,
    convert_to_svg=False
):
    """Create blank image of certain width, height and col."""
    if ext is None:
        ext = environ["default_img_format"]
    img = Image.new(mode, (width, height), col)
    if convert_to_svg:
        img = Image.new(mode, (width, height), black_col)
    img.save(fname + ext)

    if convert_to_svg:
        ext = svg_convert(fname, ext, col)

    return ImageProps(fname, ext, width, height)


def concat_images(horizontal, img1, img2, margin=None, **kwargs):
    """Concatenate two svgs."""
    # Beef up Kwargs
    direction = "v"
    if horizontal:
        direction = "h"

    optional_kwargs = {
        fname_key: img1[fname_key] + img2[fname_key],
        ext_key: img1[ext_key]
    }
    for k, v in optional_kwargs.items():
        try:
            kwargs[k]
        except KeyError:
            kwargs[k] = v

    for k, v in img1.items():
        try:
            kwargs[k]
        except KeyError:
            kwargs[k] = v

    # Run svg stack
    c = ["svg_concat", "--direction", direction]
    c.extend(["--dest", kwargs[fname_key] + kwargs[ext_key]])
    if margin:
        c.extend(["--margin", margin])
    imgs = [img1, img2]
    for i in imgs:
        c.append(i[fname_key] + i[ext_key])
    subprocess.run(c)

    # Create resulting Image Properties
    concat_image_props = kwargs
    if horizontal:
        additive_keys = [width_key]
    else:
        additive_keys = [height_key]
    for a in additive_keys:
        concat_image_props[a] = img1[a] + img2[a]

    return ImageProps(**concat_image_props)


def rotate_img(amount, expand=True, width_pad=0, height_pad=0, **img_props):
    """Rotate image "amount" degrees."""
    background_color = img_props[back_col_key]
    width = img_props[width_key]
    height = img_props[height_key]
    img_fname = img_props[fname_key] + img_props[ext_key]

    original = Image.open(img_fname)
    max_dim = max(width, height)
    buff = 5
    square = Image.new(
        default_color_mode,
        (max_dim + buff * 2, max_dim + buff * 5),
        background_color
    )
    square.paste(
        original,
        (
            (max_dim - width) // 2 + buff,
            (max_dim - height) // 2 + buff
        )
    )
    square = square.rotate(amount, expand=expand)

    blank_img = Image.new(
        default_color_mode,
        (height + width_pad, width + height_pad),
        background_color
    )
    blank_img.paste(square, (-(max_dim - height) // 2 - buff, -buff))

    img_props[width_key], img_props[height_key] = blank_img.size
    blank_img.save(img_fname)
    return ImageProps(**img_props)


def svg_convert(fname, ext, svg_col=None, skip_remove=False, rename=""):
    """Convert fname to svg."""
    c = ["convert_to_svg", fname + ext]
    if svg_col:
        c.append("-c")
        c.append(encode_hex_col(svg_col))
    if skip_remove:
        c.append("-s")
    if rename:
        c.append("-r")
        c.append(rename)

    subprocess.run(c)
    return ".svg"


def add_border_to_img(im, col):
    """Add border to py pillow obj."""
    width, height = im.size
    pixels = im.load()
    for x in range(width):
        pixels[x, 0] = col
        pixels[x, height - 1] = col

    for y in range(height):
        pixels[0, y] = col
        pixels[width - 1, y] = col


def make_lean_image(
    fname,
    text,
    background_color=white_col,
    text_color=black_col,
    font_name=None,
    font_size=None,
    ext=None,
    convert_to_svg=False,
    require_even=False,
    final_size=None,
    svg_col=None,
    start_height=0,
    start_width=0,
    text_seperation=lambda x: 0,
    image_props=None,
    horizontal=False,
    add_border=True,
):
    """Make image which is just large enough to contain text."""
    # Determine Image Width and Height
    if image_props is None:
        kargs = dict(
            text_seperation=text_seperation,
            font_name=font_name,
            font_size=font_size,
            horizontal=horizontal
        )
        width, height, wh, image_font = determine_min_image_size(text, **kargs)
    else:
        width, height, wh, image_font = image_props
    if require_even:
        if width % 2:
            width += 1
        if height % 2:
            height += 1

    # Draw Image
    if ext is None:
        ext = environ["default_img_format"]
    curr_height = start_height
    curr_width = start_width
    if not convert_to_svg:
        im = Image.new(default_color_mode, (width, height), background_color)
        d = ImageDraw.Draw(im)
    previous_image = None
    last_index = len(wh) - 1
    for i, (t, tw, th, sx, sy, col) in enumerate(wh):
        if convert_to_svg:
            curr_width = curr_height = 0

        if horizontal:
            dims = (sx + curr_width, sy)
            curr_width += tw
            if i < last_index:
                curr_width += text_seperation(tw)
            else:
                if require_even:
                    curr_width += 1

        else:
            dims = (sx + (width - tw) / 2, sy + curr_height)
            curr_height += th
            if i < last_index:
                curr_height += text_seperation(th)
            else:
                if require_even:
                    curr_height += 1

        if convert_to_svg:
            if curr_height == 0:
                curr_height = height
            if curr_width == 0:
                curr_width = width
            im = Image.new(
                default_color_mode,
                (curr_width, curr_height),
                background_color
            )
            d = ImageDraw.Draw(im)

        if convert_to_svg:
            img_col = text_color
            if not col:
                col = svg_col
        else:
            img_col = col
            if not col:
                img_col = text_color

        d.text(dims, t, font=image_font, fill=img_col)

        if convert_to_svg:
            tmp_fname = "tmp" + str(i)
            if i == last_index and not previous_image:
                tmp_fname = fname

            if add_border:
                add_border_to_img(im, background_color)
            im.save(tmp_fname + ext)
            svg_ext = svg_convert(tmp_fname, ext, col)
            ip = ImageProps(
                tmp_fname,
                svg_ext,
                curr_width,
                curr_height,
                **{back_col_key: background_color}
            )
            if previous_image:
                if i == last_index:
                    tmp_fname = fname
                previous_image = concat_images(
                    horizontal,
                    previous_image,
                    ip,
                    **{fname_key: tmp_fname}
                )
            else:
                previous_image = ip
            ret = previous_image

    # Save image and optionally convert to svg
    if not convert_to_svg:
        if add_border:
            add_border_to_img(im, background_color)

        if final_size:
            s = (width, height)
            f_w, f_h = final_size
            i = final_size.index(min(final_size))
            scale_factor = final_size[i] / s[i]

            print(i, scale_factor, width, height)
            s_w, s_h = (ceil(width * scale_factor), ceil(height * scale_factor))
            im = im.resize((s_w, s_h))

            print("final", (f_w, f_h), "scaled", (s_w, s_h), "position", ((f_w - s_w) // 2, (f_h - s_h) // 2))
            true_final_img = Image.new(default_color_mode, (f_w, f_h), transparent_col)
            true_final_img.paste(im, ((f_w - s_w) // 2, (f_h - s_h) // 2))

            im = true_final_img
            width, height = final_size

        im.save(fname + ext)
        ret = ImageProps(
            fname,
            ext,
            width,
            height,
            **{back_col_key: background_color}
        )

    return [ret]
