#!/usr/bin/env bash
# 使い方:
#   ./resize.sh -w 800 file1.jpg file2.png
#   ./resize.sh -h 600 *.jpg

set -e

usage() {
  echo "Usage: $0 -w WIDTH | -h HEIGHT files..."
  exit 1
}

# 引数パース
while getopts "w:h:" opt; do
  case "$opt" in
    w) SIZE="${OPTARG}x"  ;;  # 横指定
    h) SIZE="x${OPTARG}"  ;;  # 縦指定
    *) usage ;;
  esac
done
shift $((OPTIND - 1))

[ -z "$SIZE" ] && usage
[ $# -eq 0 ]   && usage

# 変換ループ
for img in "$@"; do
  dir=$(dirname "$img")
  base=$(basename "$img")
  name="${base%.*}"
  ext="${base##*.}"

  # 変換
  convert "$img" -resize "$SIZE" "${dir}/${name}_resized.${ext}"
  echo "→ ${dir}/${name}_resized.${ext}"
done

