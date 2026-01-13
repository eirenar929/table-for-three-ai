import asyncio
import time
from typing import Dict,Any,Callable,Optional,Awaitable
class ResponseBuffer:
 def __init__(self,timeout:float=8.0,min_responses:int=1):
  self.buffer:Dict[str,Dict[str,Any]]={}
  self.timeout=timeout
  self.min_responses=min_responses
  self.callbacks:Dict[str,Callable[[Dict[str,Any]],Awaitable[None]]]={}
  self.lock=asyncio.Lock()
  self.monitoring={"total_requests":0,"completed":0,"timedout":0,"avg_response_time":0.0}
 async def add_response(self,request_id:str,model_id:str,response:str):
  async with self.lock:
   if request_id not in self.buffer:
    self.buffer[request_id]={"responses":{},"start_time":time.time()}
    self.monitoring["total_requests"]+=1
    asyncio.create_task(self.start_timeout(request_id))
   self.buffer[request_id]["responses"][model_id]={"response":response,"timestamp":time.time()}
  await self.check_completion(request_id)
 def set_callback(self,request_id:str,callback:Callable[[Dict[str,Any]],Awaitable[None]]):
  self.callbacks[request_id]=callback
 async def check_completion(self,request_id:str):
  async with self.lock:
   if request_id not in self.buffer:return
   if len(self.buffer[request_id]["responses"])>=self.min_responses:await self.publish_results(request_id)
 async def start_timeout(self,request_id:str):
  await asyncio.sleep(self.timeout)
  async with self.lock:
   if request_id in self.buffer:
    self.monitoring["timedout"]+=1
    await self.publish_results(request_id)
 async def publish_results(self,request_id:str):
  if request_id not in self.buffer:return
  data=self.buffer.pop(request_id)
  if data["responses"]:
   elapsed=time.time()-data["start_time"]
   total=self.monitoring["completed"]
   self.monitoring["avg_response_time"]=(total*self.monitoring["avg_response_time"]+elapsed)/(total+1)
   self.monitoring["completed"]+=1
  callback=self.callbacks.pop(request_id,None)
  if callback:asyncio.create_task(callback(data["responses"]))
 def get_stats(self)->Dict[str,Any]:
  return {**self.monitoring,"success_rate":self.monitoring["completed"]/max(self.monitoring["total_requests"],1),"active_requests":len(self.buffer)}
