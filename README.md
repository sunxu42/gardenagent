1. 使用conda 新建python环境
2. cd gardenAgent
3. 运行安装命令 pip install -e .

4. 启动mcp 服务器 
```
cd gardenAgent/brain_langchain
python mcp_server.py 
```
5. 运行demo，命令行对话
```
cd gardenAgent/brain_langchain

python scenario_one.py 
```

6. 启动webscoket 服务端
```
python server.py
```

7. 启动web聊天demo

```
streamlit run webapp.py
```
 