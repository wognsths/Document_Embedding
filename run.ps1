$ticker = "005930"

# 2019년부터 2025년까지 반복 실행
foreach ($year in 2019..2025) {
    Write-Output "[$year] Crawler Running..."
    python -m Collection.Crawler.Stock.crawling -t $ticker -y $year
    Write-Output "[$year] Ended."
}
