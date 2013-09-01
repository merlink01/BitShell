#!/usr/bin/env python
import os
import sys
import logging
import cmd
import datetime
import signal
import class_api
log = logging.getLogger('bitshell')

#A hack to let pybitmessage source directory exist in bitshell sourcedir
if os.path.exists(os.path.abspath('src')):
    sys.path.append(os.path.abspath('src'))
    
#html2text
import html2text
if float(html2text.__version__) < float(3.1):
    print 'html2text Version > 3.0 is required'
    sys.exit(1)
html2text.IGNORE_ANCHORS = True
html2text.IGNORE_IMAGES = True

#readline support will run if we get all prints out of bitmessage
USING_READLINE = True
try:
    import readline
    try:
        if sysinfo['system'] == 'windows':
            readline.rl.mode.show_all_if_ambiguous="on" #config pyreadline on windows
    except:
        pass
except:
    USING_READLINE = False

class BitShell(cmd.Cmd):

    def __init__(self):
        cmd.Cmd.__init__(self)
        signal.signal(signal.SIGINT, self.do_exit)
        
        self.stdoutEncoding = sys.stdout.encoding or locale.getpreferredencoding()
        self.api = class_api.getAPI(silent=True)

        if not USING_READLINE:
            self._print('No readline Support detected, Autocompletion is not available on your system.')
            self._print('You can install pyreadline to get it running.')
            self.completekey = None
            
        log.info('Starting BitShell')
        self.prompt = 'BitShell :'
        self._print('#'*80)
        self._print(30 * ' ' + 'Welcome to BitShell')
        self._print('#'*80)
        self._print('Enter: help or help <command> to get more information')
        self._print('')
        self.messages = {}
        self.sentMessages = []

    def do_ls(self, *args):
        
        """List all BitMessages"""
        
        messages = self.api.getAllInboxMessages()
        counter = 0
        self.messages = {}
        for message in messages:
            counter += 1
            msgid = message['msgid']
            title = message['subject'].decode('utf-8').replace('\n',' ')
            self.messages[counter] = msgid
            if message['read'] == 1:
                read = 'r'
            else:
                read = 'u'
            self._print('%03d:[%s] [%s]%s'%(counter,read,datetime.datetime.utcfromtimestamp(int(message['receivedTime'])),title))
            
        self._print('')
        
        
    def do_read(self,num):
        
        """Print a Message by Number"""
        
        if num == '':
            self._print('Please enter the Message Number')
            return
            
        try:
            num = int(num)
        except:
            self._print('Please enter the Message Number')
            return
            
        if not num in self.messages:
            self._print('Message Number: %s doesnt exist'%num)
            return
            
        messages = self.api.getAllInboxMessages()
        
        for message in messages:
            if message['msgid'] == self.messages[num]:
                self._print('Recieved from: %s at %s'%(message['fromAddress'],datetime.datetime.utcfromtimestamp(int(message['receivedTime']))))
                self._print('#'*80)
                self._print(message['subject'].decode('utf-8'))
                self._print('#'*80)
                self._print('\n')
                try:
                    self._print(html2text.html2text(message['message'].decode('utf-8')))
                except:
                    self._print(message['message'].decode('utf-8'))
                
                self._print('#'*80)
                self.api.markInboxMessageAsRead(message['msgid'])
                return

    def do_del(self,num):
        
        """Delete a message by Number"""
        
        if num == '':
            self._print('Please enter the Message Number')
            return
            
        try:
            num = int(num)
        except:
            self._print('Please enter the Message Number')
            return
            
        if not num in self.messages:
            self._print('Message Number: %s doesnt exist'%num)
            return

        self.api.trashInboxMessage(self.messages[num])
        self._print('Trashed: %s'%self.messages[num])
        del self.messages[num]
    
    def do_write(self,*args):
        
        """Write a Bitmessage"""
        
        addresses = self.api.listAddresses()
        while 1:
            self._print('Please Enter your Sending Address Number:\n')

            counter = 0
            addlist = {}
            
            for add in addresses:
                counter += 1
                self._print('%03d: %s - %s'%(counter,add['label'],add['address']))
                addlist[counter] = add['address']
            
            self.stdout.write('#')
            data = raw_input()

            if data == '':
                continue
                
            try:
                data = int(data)
            except:
                self._print('%s is not correct \n'%data)
            
            if not data in addlist:
                self._print('%s is not correct \n'%data)
                continue
            break
            
        mfrom = addlist[data]
        
        toaddresses = self.api.listContacts()
        while 1:
            self._print('Please Enter your Contact to send:\n')

            counter = 0
            addlist = {}
            
            for add in toaddresses:
                counter += 1
                self._print('%03d: %s - %s'%(counter,add['label'],add['address']))
                addlist[counter] = add['address']
            
            self.stdout.write('#')
            data = raw_input()

            if data == '':
                continue
                
            try:
                data = int(data)
            except:
                self._print('%s is not correct \n'%data)
            
            if not data in addlist:
                self._print('%s is not correct \n'%data)
                continue
            break
        
        mto = addlist[data]
        
        self._print('Writing from: %s to %s'%(mfrom,mto))
        
        self._print('Please Enter the subject:')
        subj = raw_input()
        
        self._print('Please Enter the Message:')
        message = raw_input()

        try:
            answer = self.api.sendMessage(mfrom,mto,subj,message)
        except:
            self._print('Sending Error, please check your Target Address')
            return
            #~ 
        if 'API Error' in answer:
            self._print(answer)
        else:
            self._print('Message Sended correct...')
        self.sentMessages.append(answer)
    
    def do_createaddress(self, name):
        
        """Create a Random Address"""
        
        if not name:
            self._print('Please Enter the Name of the Address:')
            name = raw_input()
        self.api.createRandomAddress(name)
        
    def _print(self,message):

        sys.stderr.write(message.encode(self.stdoutEncoding) + '\n')

    def emptyline(self):

        """This method prevent the Shell from repeating last
        command by pressing enter a second time"""
        
        return

    def do_exit(self, *args):

        """Exit this Shell
        Usage: exit"""

        self._print('Exiting...')
        self.api.stop()
        os._exit(0)

    def cmdloop(self, intro=None):
        """Repeatedly issue a prompt, accept input, parse an initial prefix
        off the received input, and dispatch to action methods, passing them
        the remainder of the line as argument.

        """

        self.preloop()
        if self.use_rawinput and self.completekey:
            try:
                import readline
                self.old_completer = readline.get_completer()
                readline.set_completer(self.complete)
                readline.parse_and_bind(self.completekey+": complete")
            except ImportError:
                pass
        try:
            if intro is not None:
                self.intro = intro
            if self.intro:
                self.stdout.write(str(self.intro)+"\n")
            stop = None
            while not stop:
                if self.cmdqueue:
                    line = self.cmdqueue.pop(0)
                else:
                    if self.use_rawinput:
                        try:
                            sys.stderr.write(self.prompt)
                            line = raw_input()
                        except EOFError:
                            line = 'EOF'
                    else:
                        self.stdout.write(self.prompt)
                        self.stdout.flush()
                        line = self.stdin.readline()
                        if not len(line):
                            line = 'EOF'
                        else:
                            line = line.rstrip('\r\n')
                line = self.precmd(line)
                stop = self.onecmd(line)
                stop = self.postcmd(stop, line)
            self.postloop()
        finally:
            if self.use_rawinput and self.completekey:
                try:
                    import readline
                    readline.set_completer(self.old_completer)
                except ImportError:
                    pass
                    
    def do_addcontact(self, name):
        
        if not name:
            self._print('Please Enter the Name of the Address:')
            name = raw_input()
            
        self._print('Please Enter Bitmessage Address:')
        adress = raw_input()
        
        respond = self.api.addContact(name,adress)
        
        if respond is not None:
            self._print(respond)
        else:
            self._print('User entered correct')

    def do_sent(self,*args):
        
        """Lists all Sent Messages and there Status"""
        
        msgs = self.api.getAllSentMessages()
        contacts = self.api.listContacts()
        counter = 0
        for msg in msgs:
            counter += 1

            printName = msg['toAddress']
            mto = msg['toAddress']
            for entry in contacts:

                if entry['address'] == mto:
                    printName = '%s(%s)'%(entry['label'], entry['address'])
                    
            self._print('%03d:%s - To:%s\nSubject:[%s]'%(counter,msg['status'],printName,msg['subject'].decode('utf-8')))
                    
    def do_status(self,*args):
        info = self.api.clientStatus()

        if int(info['networkConnections']) < 1:
            self._print('Not Connected')
        else:
            self._print('Connected to %s clients'%info['networkConnections'])
        
if __name__ == '__main__':
    x = logging.getLogger('flexfs')
    fmt_string = "[%(levelname)-7s]%(asctime)s.%(msecs)-3d %(module)s[%(lineno)-3d]/%(funcName)-15s  %(message)-8s "
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(fmt_string,"%H:%M:%S"))
    x.addHandler(handler)
    x.setLevel(logging.DEBUG)
    
    BitShell().cmdloop()
