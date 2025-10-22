from typing import Optional
import qrcode
from qrcode.constants import ERROR_CORRECT_M
from PIL import Image
import sys

"""
qrCodeGen.py

Simple helper to generate and display a QR code from a string.

Dependencies:
    pip install qrcode[pil]
"""



def make_qr(
        text: str,
        box_size: int = 10,
        border: int = 4,
        fill_color: str = "black",
        back_color: str = "white",
        save_path: Optional[str] = None,
        show: bool = True,
) -> Image.Image:
        """
        Create a QR code image from `text`.

        Args:
            text: string to encode into the QR code.
            box_size: pixel size of each QR box (default 10).
            border: border width in boxes (default 4).
            fill_color: color for the QR modules (default "black").
            back_color: background color (default "white").
            save_path: optional path to save the generated image (PNG will be used).
            show: if True, open the image with the default image viewer.

        Returns:
            PIL Image object containing the generated QR code.
        """
        if not isinstance(text, str) or text == "":
                raise ValueError("text must be a non-empty string")

        qr = qrcode.QRCode(
                version=None,
                error_correction=ERROR_CORRECT_M,
                box_size=box_size,
                border=border,
        )
        qr.add_data(text)
        qr.make(fit=True)

        img = qr.make_image(fill_color=fill_color, back_color=back_color).convert("RGB")

        if save_path:
                img.save(save_path)

        if show:
                img.show()

        return img


if __name__ == "__main__":
        # quick demo when run as a script

        sample = "https://bjt426ms-5000.use.devtunnels.ms/" if len(sys.argv) == 1 else " ".join(sys.argv[1:])
        make_qr(sample, show=True, save_path="sample_qr.png")