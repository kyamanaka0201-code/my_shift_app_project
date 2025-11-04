
# シフト管理システム

従業員のシフト自動生成と給与計算を行うWebアプリケーション

## 🌐 デモサイト
https://my-shift-app-project.onrender.com/shift_matrix/

※ 無料ホスティングのため、初回アクセス時は起動に1-2分かかります。「Bad Gateway」が表示された場合は、少々お待ちいただき再読み込みをお願いします。

## 📸 スクリーンショット

### シフト表画面
![シフト表](screenshots/shift_matrix.png)

### 給与グラフ
![給与グラフ](screenshots/salary_graph.png)

### 給与グラフ
![給与グラフ](screenshots/salary_graph2.png)

### 管理画面
![管理画面](screenshots/admin_panel.png)

## ⚙️ 技術スタック
- **バックエンド**: Python, Django 5.2
- **データベース**: PostgreSQL
- **フロントエンド**: HTML, CSS, JavaScript
- **データ可視化**: Matplotlib, japanize-matplotlib
- **デプロイ**: Render

## ✨ 主な機能
- シフトの自動生成（勤務日数・連続勤務制約を考慮）
- 月別シフト表の表示
- 給与グラフの可視化
- Excel/CSV形式でのエクスポート
- 管理者画面での従業員管理

## 📝 開発の背景
飲食店のシフト管理を効率化するために開発しました。手動でのシフト作成の手間を削減し、公平なシフト配分を実現することを目指しています。