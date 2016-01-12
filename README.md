lr2irproxy
======================
LR2IRに対するHTTP通信をいじったり監視したり乗っ取ったりできるHTTPサーバ+プロキシサーバ

動作要件
----------------
Python2.7.x (https://www.python.org/)

lxml (http://lxml.de/)

`127.0.0.1:80`で他のサーバ等を立てていないこと。

作者は Python2.7.9 + lxml3.5.0 on Win7HPx64 でのみ動作確認

使い方
----------------
lr2irproxy.pyが含まれるフォルダーをLR2beta3ディレクトリ直下に設置し、
lr2irproxy.pyを実行(ダブルクリック)する。

終了はCtrl+Cで行える。

ライバル内ランキング等についての注意
----------------
Webブラウザを経由する通信のみをいじりたいのであれば、たとえばWebブラウザの自動構成スクリプトを
```javascript
function FindProxyForURL(url, host){
  if (host == "www.dream-pro.info"){
    return "PROXY 127.0.0.1:80";
  else{
    return "DIRECT";
  }
} 
```
のように書けばlr2irproxyを使うようになる。

LR2body.exeの通信をlr2irproxyに渡すためにはwww.dream-pro.infoへの通信を127.0.0.1に渡す必要がある。

ひとつの方法として、hostsファイルに以下のエントリを加える方法がある。
```
127.0.0.1 www.dream-pro.info
```
自己責任でお願いします。

ライセンス
----------
The MIT License (MIT)

Copyright (c) 2015 @GNQG

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
