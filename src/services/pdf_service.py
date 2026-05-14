from __future__ import annotations

from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape, portrait
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Image as RLImage
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from src.models.block import BlockContext
from src.services.cache_service import CacheService
from src.utils.file_utils import ensure_dir


class PdfService:
    def __init__(self, settings: dict[str, Any], cache_service: CacheService):
        self.settings = settings
        self.cache_service = cache_service
        self.pdf_cfg = settings.get("pdf", {})

    def ensure_pdf(self, ctx: BlockContext) -> BlockContext:
        skip, path, from_cache = self.cache_service.should_skip_pdf(ctx.record)
        if skip and path:
            ctx.pdf_path = path
            ctx.cached_pdf = from_cache
            return ctx

        if ctx.map_path is None:
            raise ValueError("BlockContext.map_path is required to build the PDF.")

        pdf_path = self.cache_service.pdf_output_path(ctx.record)
        ensure_dir(pdf_path.parent)
        self._build_pdf(ctx, pdf_path)
        self.cache_service.save_pdf_copy_to_cache(ctx.record, pdf_path)
        ctx.pdf_path = pdf_path
        ctx.cached_pdf = False
        return ctx

    def _build_pdf(self, ctx: BlockContext, pdf_path: Path) -> None:
        page_size = self._page_size()
        margins = self.pdf_cfg.get("margins", {})
        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=page_size,
            leftMargin=float(margins.get("left", 30)),
            rightMargin=float(margins.get("right", 30)),
            topMargin=float(margins.get("top", 28)),
            bottomMargin=float(margins.get("bottom", 20)),
        )

        story = []
        if self.pdf_cfg.get("title", {}).get("enabled", False):
            title_cfg = self.pdf_cfg["title"]
            styles = getSampleStyleSheet()
            title_style = styles["Title"]
            title_style.fontName = title_cfg.get("font_name", "Helvetica-Bold")
            title_style.fontSize = int(title_cfg.get("font_size", 14))
            text = title_cfg.get("text_template", "Bloque {block_id}").format(
                block_id=ctx.record.block_id,
                country=ctx.record.country,
            )
            story.append(Paragraph(text, title_style))
            story.append(Spacer(1, 6))

        if self.pdf_cfg.get("table", {}).get("enabled", True):
            story.append(self._table(ctx))
            story.append(Spacer(1, float(self.pdf_cfg.get("image", {}).get("space_before", 12))))

        image_cfg = self.pdf_cfg.get("image", {})
        img = RLImage(
            str(ctx.map_path),
            width=float(image_cfg.get("width", 780)),
            height=float(image_cfg.get("height", 470)),
        )
        story.append(img)
        doc.build(story)

    def _page_size(self):
        size = A4
        orientation = self.pdf_cfg.get("orientation", "landscape")
        return landscape(size) if orientation == "landscape" else portrait(size)

    def _table(self, ctx: BlockContext) -> Table:
        fields = self.settings.get("table_fields", [])
        headers = [item.get("label", item.get("source")) for item in fields]
        row = [str(ctx.record.get(str(item["source"]).upper(), "")) for item in fields]
        data = [headers, row]

        available_width = self._page_size()[0] - float(self.pdf_cfg.get("margins", {}).get("left", 30)) - float(self.pdf_cfg.get("margins", {}).get("right", 30))
        col_width = available_width / max(len(headers), 1)
        table = Table(data, colWidths=[col_width] * len(headers), hAlign="CENTER")

        tbl_cfg = self.pdf_cfg.get("table", {})
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(tbl_cfg.get("header_background", "#15253C"))),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor(tbl_cfg.get("header_text_color", "#FFFFFF"))),

                    ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                    ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#1F2937")),

                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTNAME", (0, 1), (-1, -1), tbl_cfg.get("font_name", "Helvetica")),

                    ("FONTSIZE", (0, 0), (-1, 0), int(tbl_cfg.get("header_font_size", 11))),
                    ("FONTSIZE", (0, 1), (-1, -1), int(tbl_cfg.get("font_size", 10))),

                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),

                    ("LINEBELOW", (0, 0), (-1, 0), 1.2, colors.HexColor("#15253C")),
                    ("LINEBELOW", (0, 1), (-1, -1), 0.35, colors.HexColor(tbl_cfg.get("border_color", "#D9E2EC"))),
                    ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor(tbl_cfg.get("border_color", "#D9E2EC"))),

                    ("TOPPADDING", (0, 0), (-1, -1), float(tbl_cfg.get("padding", 7))),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), float(tbl_cfg.get("padding", 7))),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        return table
