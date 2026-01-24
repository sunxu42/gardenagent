1. 使用conda 新建python环境
```
conda create -n myenvname python=3.12
pip install -r requirements.txt
conda install pygraphviz

```
2. 启动mcp 服务器 
```
cd yard/brain_langchain
python mcp_server.py 
```

3. 启动webscoket 服务端
```
python server.py
```
4. 启动web聊天demo
   - 浏览器打开 test文件夹内网页
 