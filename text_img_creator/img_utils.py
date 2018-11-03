"""Pillow extensions."""
from collections.abc import MutableMapping
import sys
import os
import subprocess

class InvalidPadding(Exception):
    """Raised on padding of length 3, or >4."""

    pass


class ImageText:
    """Store image text properties."""

    valid_paddings = set([4, 2, 1])
    padding_max_size = 4

    def __init__(
        self,
        text,
        target_width=None,
        target_height=None,
        padding=(0,),
        color=None,
        sx=None,
        sy=None
    ):
        """Initialize properties."""
        l = len(padding)
        if l not in self.valid_paddings:
            raise InvalidPadding
        mult = self.padding_max_size // l
        full_padding = []
        for p in padding:
            for i in range(mult):
                full_padding.append(p)

        self.padding = full_padding
        self.text = str(text)
        self.target_width = target_width
        self.target_height = target_height
        self.color = color
        self.sx = sx
        self.sy = sy
        self.width = target_width
        self.height = target_height

    def __str__(self):
        """Return text prop."""
        return self.text

    def __repr__(self):
        """Return text, width, height target."""
        return "<" + self.text + " target_width " + str(self.target_width) + " target_height " + str(self.target_height) + ">"

    def __iter__(self):
        """Iterate through object items."""
        return iter([self.text, self.width, self.height, self.sx, self.sy, self.color])

class ImageProps(MutableMapping):
    """Store Image properties."""

    fname_key = "fname"
    ext_key = "ext"
    width_key = "width"
    height_key = "height"
    back_col_key = "background_color"

    def __init__(self, fname, ext, width, height, **kwargs):
        """Set initial properties."""
        d = {
            ImageProps.fname_key: fname,
            ImageProps.ext_key: ext,
            ImageProps.width_key: width,
            ImageProps.height_key: height
        }
        self._storage = {**d, **kwargs}

    def __getitem__(self, key):
        """Get item from storage."""
        return self._storage[key]

    def __delitem__(self, key):
        """Del key."""
        del self.storage[key]

    def __setitem__(self, key, item):
        """Set key to item."""
        self._storage[key] = item

    def __iter__(self):
        """Iter over storage."""
        return iter(self._storage)

    def __len__(self):
        """Get len of storage."""
        return len(self._storage)

    def __str__(self):
        """Get string of storage."""
        return str(self._storage)


def run_command_on_imgs(create_command, apply_command_to_img=lambda x, y: True, source_dir_path=None, types=None):
    if types is None:
        types = [".png"]

    fname_iter = None
    if len(sys.argv) > 1:
        fname_iter = sys.argv
    else:
        fname_iter = [os.path.join(source_dir_path, fname_and_extension) for fname_and_extension in os.listdir(source_dir_path)]

    output = []
    for fname_and_extension in fname_iter:
        fname, fext = os.path.splitext(fname_and_extension)
        if apply_command_to_img(fname, fext) and fext in types:
            output_file, command = create_command(fname, fext)
            subprocess.run(command)
            output.append(output_file)
    return output
