import qrcode

url = "https://unmixable-oxygen-flannels.ngrok-free.dev"

img = qrcode.make(url)

img.save("qr.png")

print("QR Code Generated!")
