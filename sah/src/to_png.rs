use image::{imageops, DynamicImage, ImageFormat, Rgba, RgbaImage};
use std::io::Cursor;
use text_to_png::TextRenderer;

/// Render the headers as a multiline PNG with a custom background color.
/// Example: `self.png_with_bg("#FFFFFF")`
pub fn png_with_bg(text: &str, bg: Rgba<u8>) -> Vec<u8> {
    // render text line by line
    let renderer = TextRenderer::default();
    let mut rendered_lines: Vec<RgbaImage> = Vec::new();
    for line in text.split('\n') {
        let png = renderer
            .render_text_to_png_data(&line, 16, "#000000")
            .unwrap();
        let img = image::load_from_memory(&png.data).unwrap().to_rgba8();
        rendered_lines.push(img);
    }

    // Find max width and total height
    let line_spacing = 6;
    let max_w = rendered_lines.iter().map(|i| i.width()).max().unwrap_or(1);
    let mut total_h: u32 = rendered_lines
        .iter()
        .map(|i| i.height() + line_spacing)
        .sum();
    total_h -= line_spacing; // last line

    // copy each line into final canvas
    let mut canvas = RgbaImage::from_pixel(max_w, total_h, bg);
    let mut y_off = 0;
    for img in rendered_lines {
        let height = img.height() as i64;
        imageops::overlay(&mut canvas, &DynamicImage::ImageRgba8(img), 0, y_off);
        y_off += height + line_spacing as i64;
    }

    let mut buf = Vec::new();
    DynamicImage::ImageRgba8(canvas)
        .write_to(&mut Cursor::new(&mut buf), ImageFormat::Png)
        .expect("encode PNG");
    buf
}
