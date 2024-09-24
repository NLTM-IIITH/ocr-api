"""
OCR API

Author: Krishna Tulsyan (kt.krishna.tulsyan@gmail.com)
"""

import uvicorn

from server.config import PORT

if __name__ == '__main__':
	uvicorn.run('server.app:app', host='0.0.0.0', port=PORT, reload=True, workers=4)
