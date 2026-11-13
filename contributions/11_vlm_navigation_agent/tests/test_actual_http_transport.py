"""Execute actual local HTTP JPEG/VLM transport, but use a deterministic mock server.

This exercises JSON request/response interoperability and safety gating.
It does NOT execute any real VLM weights, image understanding or physical robot.
"""
from __future__ import annotations
import base64
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from vlm_planner import VLMNavigationPlanner,VLMPlannerConfig

class RequestHandler(BaseHTTPRequestHandler):
    calls=[]
    def do_POST(self):
        n=int(self.headers["Content-Length"])
        payload=json.loads(self.rfile.read(n))
        RequestHandler.calls.append({"path":self.path,"payload":payload})
        goal={"region":"corridor","goal":"move forward","confidence":.91,"pixel_u":8,"pixel_v":8}
        if self.path=="/api/chat":
            response={"message":{"content":json.dumps(goal)}}
        elif self.path=="/v1/chat/completions":
            response={"choices":[{"message":{"content":json.dumps(goal)}}]}
        else:
            self.send_error(404)
            return
        data=json.dumps(response).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",str(len(data)))
        self.end_headers()
        self.wfile.write(data)
    def log_message(self,*args):
        pass

def test_actual_local_http_roundtrips_for_both_request_schemas():
    RequestHandler.calls=[]
    server=ThreadingHTTPServer(("127.0.0.1",0),RequestHandler)
    thread=threading.Thread(target=server.serve_forever,daemon=True)
    thread.start()
    try:
        frame=np.zeros((32,32,3),dtype=np.uint8)
        depth=np.ones((32,32),dtype=np.float32)*2
        for suffix in ("/api/chat","/v1/chat/completions"):
            cfg=VLMPlannerConfig(api_endpoint=f"http://127.0.0.1:{server.server_port}"+suffix,
                                 require_metric_waypoint=True,max_retries=1)
            planner=VLMNavigationPlanner(cfg)
            goal=planner.plan(frame,depth_frame=depth)
            assert goal is not None
            assert goal.region_label=="corridor"
            assert goal.metric_waypoint is not None
        assert len(RequestHandler.calls)==2
        for request in RequestHandler.calls:
            user=request["payload"]["messages"][1]
            if request["path"]=="/api/chat":
                encoded=user["images"][0]
            else:
                content=user["content"]
                assert content[0]["type"]=="text"
                encoded=content[1]["image_url"]["url"].split(",",1)[1]
            assert base64.b64decode(encoded).startswith(b"\xff\xd8\xff"),"must be genuine JPEG bytes"
    finally:
        server.shutdown()
        thread.join(timeout=4)
        server.server_close()
