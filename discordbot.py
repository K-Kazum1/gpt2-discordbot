import asyncio
import discord
from discord.ext import commands
import os,datetime,numpy as np,json,re,sys,time
import gpt_2,tensorflow as tf
import re




sess = gpt_2.start_tf_sess()
print(gpt_2.load_gpt2(sess))

checkpoint_path = os.path.join('models', '345M')
enc=gpt_2.encoder.get_encoder(checkpoint_path)

hparams = gpt_2.model.default_hparams()
with open(os.path.join(checkpoint_path, 'hparams.json')) as f:
        hparams.override_from_dict(json.load(f))
context = tf.compat.v1.placeholder(tf.int32, [1, None])



bot = commands.Bot(command_prefix='none')

f=open("bot.txt")
bot_token=f.read()

emojis=dict()
imitates=dict()
session=dict()
messages=dict()
messagequeue=dict()

tf_sample = gpt_2.sample.sample_sequence(
            hparams=hparams,
            length=728,
            context=context,
            batch_size=1,
            temperature=0.9,
            top_k=40)



non_bmp_map = dict.fromkeys(range(0x10000, sys.maxunicode + 1), 0xfffd)
pad         = lambda a:'0'+str(a) if  a<10 else str(a)
datef       = lambda a: pad(a.day)+'-'+str('Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split(' ')[a.month-1])+'-'+str(a.year%100)+' '+pad(a.hour%12)+':'+pad(a.minute)+(' PM' if a.hour>12 else ' AM')
parse       = lambda message,attachments=None:f'[{datef(message.created_at-datetime.timedelta(seconds=3600*4))}] {message.author}\n{message.clean_content}\n\n'
getemoji    = lambda a: (a[2:a[2:].find(':')+2],a[-a[::-1].find(':'):-1])

@bot.event
async def on_ready():
    for f in open('emojis.txt','r'):
        a=f.split(')^@*')
        emojis[a[0]]=int(a[1][:-1])
    print('Bot online!')

def parse(message):
    try:
        a=message.clean_content
        for i in re.findall('<:.+?:[0-9]+>',a):
            a=a.replace(i,f':{getemoji(i)[0]}:')

        emb=embeds(message)
        att=attachments(message)
        embatt=("" if emb+att=="" else "\n")+emb+att+("" if emb+att=="" else "\n")
        return f'[{datef(message.created_at-datetime.timedelta(seconds=3600*0))}] {message.author}\n{a}\n{embatt}\n'        
    except:
        try:
            time=datef(message.created_at-datetime.timedelta(seconds=3600*0))
        except:
            time="[01-Jan-20 00:00 AM]"
        try:
            aut=str(message.author).translate(non_bmp_map)
        except:
            aut="Deleted User#0000"
        try:
            msg=message.clean_content.translate(non_bmp_map)
        except:
            msg="He11o"
        return '['+time+'] '+aut+'\n'+ msg+'\n\n'

def dateparse(a):
    datetime.datetime(*map(int,a.split(',')))            

def addchannel(message,replylist):
    if int(message.channel.id) not in replylist:
        replylist.add(int(message.channel.id))
        open('replychannel.txt','a',errors='ignore').write(str(message.channel.id)+'\n')
    return replylist

def removechannel(message,replylist):
    replylist.discard(message.channel.id)
    a=open('replychannel.txt','w',errors='ignore')
    for i in replylist:
        a.write(str(i)+'\n')
    return replylist

@bot.event
async def on_message(message):
    if type(message)==list:
        message=message[0]
        edit=True
    else:
        edit=False
    name=f'{message.guild}{message.channel}'
    if name in messagequeue:
        if type(messagequeue[name])!=str:
            messagequeue[name].close()
    if f'{message.guild}{message.channel}' not in channel_ids:
        open('channelids.txt','a').write(f'\n{message.guild}{message.channel}\n{message.channel.id}')
        channel_ids[f'{message.guild}{message.channel}']=f'{message.channel.id}'

    if f'{message.author}' not in user_ids:
        open('userids.txt','a').write(f'\n{message.author}\n{message.author.id}')
        user_ids[f'{message.author}']=f'{message.author.id}'
    
    for i in re.findall('<:.+?:[0-9]+>',message.clean_content):
        emoji=getemoji(i)
        if emoji[0] not in emojis:
            open('emojis.txt','a',errors='ignore').write(f'\n{emoji[0]}\n{emoji[1]}')
            emojis[emoji[0]]=int(emoji[1])


    messagequeue[name]= await bot.loop.run_in_executor(None,handle_message,[message,edit])
    
    
        

    try:
        await messagequeue[name]
        await bot.change_presence(status=discord.Status.idle,activity=None)
        if name in messagequeue:
            messagequeue.pop(name)
    except:
        pass
    
@bot.event
async def on_message_edit(before,after):
    if before.clean_content==after.clean_content and len(before.embeds)<len(after.embeds):
        await on_message([after])
        

def gen(tf_sample,q):
    return sess.run(tf_sample,feed_dict={context:[q]})[0]

async def handle_message(message):
    message,edit=message
    try: 
        replyfile=open('replychannel.txt','r',errors='ignore')
        reply='a'
        replylist=set()
        while reply!='':
            reply=replyfile.readline()[:-1]
            if reply.isdigit():
                replylist.add(int(reply))
        
        if(not message.author.bot):
            msg=message.clean_content.split(' ')
            if len(msg)>=2:
                if msg[0].lower()=='bot':
                    if msg[1]=='add':
                        replylist=addchannel(message,replylist)
                    elif msg[1]=='remove':
                        replylist=removechannel(message,replylist)
                    elif msg[1]=='imitate':
                        if re.search('.+#[0-9]{4}',' '.join(msg[2:])):
                            imitates[message.channel.id]=' '.join(msg[2:])
                            
                        
        if message.clean_content!='' and (not message.author.bot) and ((message.channel.id in replylist) or type(message.channel)==discord.DMChannel):
            async with message.channel.typing():
                await bot.change_presence(status=discord.Status.dnd, activity=discord.Game(f"Responding to {len(messagequeue)} messages"))
                c=''
                if message.channel.id not in messages:
                    messages[message.channel.id]=[]
                if len(messages[message.channel.id])<15:
                    try:
                        msgs=await message.channel.history(limit=15-len(messages[message.channel.id])).flatten()
                        for message in msgs[::-1]:
                            messages[message.channel.id].append(parse(message))
                    except:
                        messages[message.channel.id].append(parse(message))
                else:
                    messages[message.channel.id].append(parse(message))
                    z=messages[message.channel.id].pop(0)

                ql=700
                if message.channel.id in imitates:
                    imitate=imitates[message.channel.id]
                else:
                    imitate=bot.user.name+str(bot.user.id)
                while ql>500:
                    c=''
                    for i in messages[message.channel.id]:
                        c+=i
                    co='['+datef(datetime.datetime.now())+'] '+imitate+'\n'
                    c+=co
                    q=enc.encode(c)
                    ql=len(q)
                    messages[message.channel.id].pop(0)
                    
                    
                
            
                q=await bot.loop.run_in_executor(None,gen,tf_sample,q)
                q=enc.decode( q[ql:])
                q=q[:q.index('[')]

                
                if message.channel.id not in imitates:
                    q=f"[{imitate[:imitate.find('#')]}]"+q
                
                elif not any([j in q for j in ['Joined the server.','<|endoftext|>']]):

                    for i in set(re.findall(':.+?:',q)):
                        if i[1:-1] in emojis:
                            q=q.replace(i,f"<{i}{emojis[i[1:-1]]}>")
                    await message.channel.send(q)
                                        
                else:
                    print('failed to send',q)
                
    except asyncio.CancelledError:
        print('asyncerror')
        return
        
bot.run('NTA0NDIzOTY2MjU3OTcxMjA0.XkR7_g.wHOGY48hPUqF8HobdXVy1aBupvI')
