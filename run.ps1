# powershell.exe -ExecutionPolicy Bypass -File .\run.ps1

$ticker = "005930"

foreach ($year in 2019..2025) {
    Write-Output "[$year] Crawler Running..."
    python -m Collection.Crawler.Stock.crawling -t $ticker -y $year
    Write-Output "[$year] Ended."
}

python -m Collection.Crawler.Stock.section_crawler

Write-Output "Preprocessing..."
python -m Collection.Preprocess.News.process_body
Write-Output "Preprocessing Ended"

foreach ($year in 2019..2025) {
    Write-Output "[$year] Embedding Started..."
    python -m Collection.Embeddings.get_embeddings -t $ticker -y $year
    Write-Output "[$year] Ended."
}