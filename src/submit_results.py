import requests
from concurrent.futures import ThreadPoolExecutor

# post massege to STA
def post_single_STA(payloads,num,url,user,password):
    resp = requests.post(url+'/s/Observations', json=payloads[num], auth=requests.auth.HTTPBasicAuth(user, password))
    print(resp.text)
    
    
# split process to sub threads and post messages in each thread
# at the same time  
def post_batch_STA(payloads,num,length,url,user,password):
    payloads=payloads[num:num+length]
    num_list=[i for i in range(0,length)]
    print('batch_started')
    with ThreadPoolExecutor(max_workers=50) as pool:
        pool.map(post_single_STA, [payloads]* length,num_list, [url] * length,[user] * length,[password] * length)
        pool.shutdown(wait=True)
        
# split process to sub threads and post messages in each thread
# at the same time  
def post_real_STA(payloads,length,url,user,password):
    num_list=[i for i in range(0,length)]
    print('batch_started')
    with ThreadPoolExecutor(max_workers=50) as pool:
        pool.map(post_single_STA, [payloads]* length,num_list, [url] * length,[user] * length,[password] * length)
        pool.shutdown(wait=True)
