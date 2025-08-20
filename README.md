# BeeBee's Library

## Quickstart
1. Create venv & install deps:
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Linux/Mac
   .venv\Scripts\activate      # Windows
   pip install -r requirements.txt
   ```

2. Run
```
    uvicorn app.main:app --reload
```

3. Open
* Add book `http://127.0.0.1:8000/add`
* Browse / Search `http://127.0.0.1:8000/books`