#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# (C) 2025 YOKOMINE Yoshihiro, STOLOC Labs. , ICHIBYTE Inc All rights reserved.
# -----------------------------------------------------------------------------
# English
# Overview:
#   `pdf_converter.py` converts PDF files into JPEG images and thumbnails,
#   supporting single-file and bulk folder processing with optional resizing.
# Preparation:
#   Ensure Poppler is installed and available in your PATH for pdf2image.
# Dependency installation:
#   All platforms (pip): `pip install pdf2image pillow`
#   Linux (Debian/Ubuntu): `sudo apt-get install poppler-utils`
#   Windows: Install Poppler from
#     `https://github.com/oschwartz10612/poppler-windows/releases` and add the
#     `bin` folder to PATH.
#   macOS (Homebrew): `brew install poppler`
# -----------------------------------------------------------------------------
# 日本語
# 概要:
#   `pdf_converter.py` は PDF ファイルを JPEG 画像やサムネイルに変換する
#   コマンドラインツールで、単一ファイル処理とフォルダ内一括処理、任意の
#   リサイズ指定に対応します。
# 事前準備:
#   pdf2image が動作するように Poppler をインストールし PATH に通してください。
# 依存関係のインストール:
#   全OS共通 (pip): `pip install pdf2image pillow`
#   Linux (Debian/Ubuntu): `sudo apt-get install poppler-utils`
#   Windows: `https://github.com/oschwartz10612/poppler-windows/releases` から
#     Poppler を入手し `bin` フォルダを PATH に追加します。
#   macOS (Homebrew): `brew install poppler`
# -----------------------------------------------------------------------------

import argparse
import os
import sys
import shutil
import glob
from pdf2image import convert_from_path
from pdf2image.exceptions import (
    PDFInfoNotInstalledError,
    PDFPageCountError,
    PDFSyntaxError
)
# Pillow は pdf2image によって内部的に使われ、直接の import は save 時のオプション等でなければ不要な場合が多い
# from PIL import Image

def get_output_basename(input_path, output_base_arg=None):
    """
    出力ファイル名のベース部分を決定します。
    output_base_argが指定されていればそれを優先し、拡張子を取り除きます。
    指定されていなければ入力ファイル名から拡張子を取り除いたものを返します。
    """
    if output_base_arg:
        return os.path.splitext(output_base_arg)[0]
    else:
        return os.path.splitext(os.path.basename(input_path))[0]

def convert_pdf_pages_to_jpeg(input_pdf, output_dir, output_filename_base, width=None, height=None):
    """
    PDFファイルの全ページをJPEGに変換して保存します。
    """
    print(f"--- PDF全ページ変換開始: {input_pdf} ---")
    print(f"  出力ディレクトリ: {output_dir}")
    print(f"  出力ファイル名ベース: {output_filename_base}")

    size_arg = None
    size_desc = "デフォルト"
    if width is not None and height is not None:
        size_arg = (width, height)
        size_desc = f"幅{width}px, 高さ{height}px"
    elif width is not None:
        size_arg = (width, None)
        size_desc = f"幅{width}px (アスペクト比維持)"
    elif height is not None:
        size_arg = (None, height)
        size_desc = f"高さ{height}px (アスペクト比維持)"
    print(f"  指定サイズ: {size_desc}")

    try:
        os.makedirs(output_dir, exist_ok=True)
        images = convert_from_path(
            input_pdf,
            dpi=300,
            fmt='jpeg',
            size=size_arg,
            thread_count=os.cpu_count() or 1
        )

        if not images:
            print(f"  エラー: {input_pdf} から画像への変換に失敗しました。", file=sys.stderr)
            return False, 0

        num_pages = len(images)
        print(f"  {num_pages} ページを検出。JPEGファイルに変換・保存します...")

        for i, img in enumerate(images):
            page_num = i + 1
            output_jpeg_filename = f"{output_filename_base}_page{page_num}.jpg"
            output_jpeg_path = os.path.join(output_dir, output_jpeg_filename)
            print(f"    ページ {page_num}/{num_pages} -> {output_jpeg_path}")
            img.save(output_jpeg_path, 'JPEG', quality=90)

        print(f"--- PDF全ページ変換完了: {input_pdf} ({num_pages}ページ) ---")
        return True, num_pages

    except (PDFInfoNotInstalledError, PDFPageCountError, PDFSyntaxError, FileNotFoundError) as e:
        print(f"  エラー ({type(e).__name__}): {input_pdf} の処理中にエラーが発生しました: {e}", file=sys.stderr)
        if isinstance(e, PDFInfoNotInstalledError):
            print("  poppler-utilsが正しくインストールされ、PATHが通っているか確認してください。", file=sys.stderr)
        return False, 0
    except Exception as e:
        print(f"  予期せぬエラー ({type(e).__name__}): {input_pdf} の処理中に発生: {e}", file=sys.stderr)
        return False, 0

def generate_pdf_thumbnail(input_pdf, output_dir, output_filename_base, thumb_width=None, thumb_height=None, thumb_suffix="_thumbnail"):
    """
    PDFファイルの1ページ目からサムネイル画像を生成して保存します。
    """
    print(f"--- サムネイル生成開始: {input_pdf} ---")
    print(f"  出力ディレクトリ: {output_dir}")
    print(f"  出力ファイル名ベース: {output_filename_base}{thumb_suffix}.jpg")

    size_arg = None
    size_desc = "デフォルト (1ページ目)"
    if thumb_width is not None and thumb_height is not None:
        size_arg = (thumb_width, thumb_height)
        size_desc = f"幅{thumb_width}px, 高さ{thumb_height}px"
    elif thumb_width is not None:
        size_arg = (thumb_width, None)
        size_desc = f"幅{thumb_width}px (アスペクト比維持)"
    elif thumb_height is not None:
        size_arg = (None, thumb_height)
        size_desc = f"高さ{thumb_height}px (アスペクト比維持)"
    print(f"  指定サムネイルサイズ: {size_desc}")

    try:
        os.makedirs(output_dir, exist_ok=True)
        images = convert_from_path(
            input_pdf,
            dpi=200, # サムネイルなので少し解像度を落としても良い場合がある
            fmt='jpeg',
            size=size_arg,
            first_page=1,
            last_page=1, # 1ページ目のみを対象
            thread_count=1 # 1ページだけなので複数スレッドは不要
        )

        if not images:
            print(f"  エラー: {input_pdf} からサムネイル画像への変換に失敗しました。", file=sys.stderr)
            return False

        output_thumb_filename = f"{output_filename_base}{thumb_suffix}.jpg"
        output_thumb_path = os.path.join(output_dir, output_thumb_filename)
        print(f"    1ページ目をサムネイルとして保存 -> {output_thumb_path}")
        images[0].save(output_thumb_path, 'JPEG', quality=85) # サムネイル品質

        print(f"--- サムネイル生成完了: {input_pdf} ---")
        return True

    except (PDFInfoNotInstalledError, PDFPageCountError, PDFSyntaxError, FileNotFoundError) as e:
        print(f"  エラー ({type(e).__name__}): {input_pdf} のサムネイル生成中にエラー: {e}", file=sys.stderr)
        if isinstance(e, PDFInfoNotInstalledError):
            print("  poppler-utilsが正しくインストールされ、PATHが通っているか確認してください。", file=sys.stderr)
        return False
    except Exception as e:
        print(f"  予期せぬエラー ({type(e).__name__}): {input_pdf} のサムネイル生成中に発生: {e}", file=sys.stderr)
        return False

def main():
    parser = argparse.ArgumentParser(
        description="PDFファイルをページごと、またはサムネイルとしてJPEGに変換するコマンドラインツール",
        formatter_class=argparse.RawTextHelpFormatter
    )
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "-i", "--input-file",
        help="処理対象の入力PDFファイルのパス (単一ファイル処理用)"
    )
    input_group.add_argument(
        "-F", "--input-folder",
        help="処理対象の入力フォルダのパス (フォルダ内の全PDFを一括処理)"
    )

    parser.add_argument(
        "-d", "--output-dir",
        help=(
            "出力先ディレクトリ。\n"
            "指定しない場合:\n"
            "  - 単一ファイル処理時: カレントディレクトリ\n"
            "  - フォルダ一括処理時: 入力フォルダと同じ場所"
        )
    )
    parser.add_argument(
        "-o", "--output-base",
        help=(
            "【単一ファイル処理時のみ有効】出力ファイル名のベースを指定します (例: 'output' または 'output.pdf')。\n"
            "指定した場合、JPEGファイル名はこのベースから生成され (例: output_page1.jpg)、\n"
            "入力PDFファイルも <ベース名>.pdf として出力ディレクトリにコピーされます (サムネイルのみモード時はPDFコピーなし)。\n"
            "指定しない場合は、入力PDFファイル名がベースとして使用されます。"
        )
    )

    page_conversion_group = parser.add_argument_group('全ページ変換オプション (サムネイルのみモード時は無効)')
    page_conversion_group.add_argument(
        "-W", "--width",
        type=int,
        help="出力JPEGの幅（ピクセル単位）。-Hと同時指定で固定サイズ。-Wのみでアスペクト比維持。"
    )
    page_conversion_group.add_argument(
        "-H", "--height",
        type=int,
        help="出力JPEGの高さ（ピクセル単位）。-Wと同時指定で固定サイズ。-Hのみでアスペクト比維持。"
    )

    thumbnail_group = parser.add_argument_group('サムネイルオプション')
    thumbnail_group.add_argument(
        "--thumbnail-only",
        action="store_true",
        help="サムネイル (1ページ目) のみを出力します。この場合、全ページ変換は行われません。"
    )
    thumbnail_group.add_argument(
        "--thumb-width",
        type=int,
        help="サムネイルの幅 (ピクセル)。--thumb-heightと同時指定で固定。--thumb-widthのみでアスペクト比維持。"
    )
    thumbnail_group.add_argument(
        "--thumb-height",
        type=int,
        help="サムネイルの高さ (ピクセル)。--thumb-widthと同時指定で固定。--thumb-heightのみでアスペクト比維持。"
    )
    thumbnail_group.add_argument(
        "--thumb-suffix",
        default="_thumbnail",
        help="サムネイルファイル名の接尾辞 (デフォルト: _thumbnail)"
    )
    parser.add_argument(
        '--version', action='version', version='%(prog)s 2.0'
    )

    args = parser.parse_args()

    # ---- 出力ディレクトリの決定 ----
    actual_output_dir = args.output_dir
    if args.input_folder: # フォルダ処理
        if not actual_output_dir:
            actual_output_dir = args.input_folder # デフォルトは入力フォルダ
    elif args.input_file: # 単一ファイル処理
        if not actual_output_dir:
            actual_output_dir = "." # デフォルトはカレントディレクトリ
    
    try:
        os.makedirs(actual_output_dir, exist_ok=True)
    except OSError as e:
        print(f"エラー: 出力ディレクトリ '{actual_output_dir}' の作成に失敗しました: {e}", file=sys.stderr)
        sys.exit(1)


    # ---- 処理対象PDFファイルのリストアップ ----
    pdf_files_to_process = []
    if args.input_file:
        if not os.path.isfile(args.input_file):
            print(f"エラー: 入力ファイルが見つかりません: {args.input_file}", file=sys.stderr)
            sys.exit(1)
        if not args.input_file.lower().endswith(".pdf"):
            print(f"エラー: 入力ファイルはPDFファイルではありません: {args.input_file}", file=sys.stderr)
            sys.exit(1)
        pdf_files_to_process.append(args.input_file)

    elif args.input_folder:
        if not os.path.isdir(args.input_folder):
            print(f"エラー: 入力フォルダが見つかりません: {args.input_folder}", file=sys.stderr)
            sys.exit(1)
        # glob を使ってサブディレクトリを含まないPDFファイルを検索
        for filepath in glob.glob(os.path.join(args.input_folder, '*.pdf')):
            if os.path.isfile(filepath): # 念のためファイルであるか確認
                 pdf_files_to_process.append(filepath)
        for filepath in glob.glob(os.path.join(args.input_folder, '*.PDF')): # 大文字拡張子も
            if os.path.isfile(filepath) and filepath not in pdf_files_to_process:
                 pdf_files_to_process.append(filepath)


        if not pdf_files_to_process:
            print(f"情報: 入力フォルダ '{args.input_folder}' 内にPDFファイルが見つかりませんでした。", file=sys.stdout)
            sys.exit(0)
        print(f"{len(pdf_files_to_process)} 件のPDFファイルを '{args.input_folder}' から検出しました。")

    # ---- 各PDFファイルの処理 ----
    total_files_processed = 0
    total_errors = 0

    for pdf_path in pdf_files_to_process:
        print(f"\n>>> 処理中のファイル: {pdf_path}")

        # 出力ファイル名のベースを決定
        # 単一ファイル処理で --output-base が指定され、かつサムネイルのみでない場合に限り、それを使用
        current_output_base_name_arg = None
        if args.input_file and args.output_base: # -i と -o が両方指定された場合
             current_output_base_name_arg = args.output_base
        
        base_name = get_output_basename(pdf_path, current_output_base_name_arg)

        success_flag = True

        if args.thumbnail_only:
            # サムネイルのみ生成
            if not generate_pdf_thumbnail(pdf_path, actual_output_dir, base_name,
                                      args.thumb_width, args.thumb_height, args.thumb_suffix):
                success_flag = False
                total_errors +=1
        else:
            # 全ページ変換を実行
            pages_converted_success, num_pages = convert_pdf_pages_to_jpeg(
                pdf_path, actual_output_dir, base_name, args.width, args.height
            )
            if not pages_converted_success:
                success_flag = False
                total_errors +=1

            # 単一ファイル処理で -o (output_base) が指定され、かつ全ページ変換が成功した場合のみPDFをコピー
            if args.input_file and current_output_base_name_arg and pages_converted_success:
                output_pdf_filename = f"{base_name}.pdf" # get_output_basenameで拡張子は除去されているので .pdf を付与
                output_pdf_path = os.path.join(actual_output_dir, output_pdf_filename)
                try:
                    print(f"  入力PDFをコピーしています: {pdf_path} -> {output_pdf_path}")
                    shutil.copy2(pdf_path, output_pdf_path)
                    print(f"  PDFのコピー完了: {output_pdf_path}")
                except Exception as e:
                    print(f"  エラー: PDFファイル '{pdf_path}' のコピー中にエラー: {e}", file=sys.stderr)
                    # PDFコピー失敗は致命的ではないとし、エラーカウントは増やさないことも考えられる
        
        if success_flag:
            total_files_processed +=1

    print("\n--- 全ての処理が完了しました ---")
    if pdf_files_to_process: # 何かしら処理対象があった場合
        print(f"処理対象ファイル数: {len(pdf_files_to_process)}")
        print(f"正常処理ファイル数: {total_files_processed - total_errors}") # 成功フラグベースだと数え方が変わる
        print(f"エラー発生ファイル数: {total_errors}")
    
    if total_errors > 0:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
