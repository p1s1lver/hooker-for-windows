import frida
import os
import io
import traceback
import base64
import platform

def withColor(string, fg, bg=49):
    print("\33[0m\33[%d;%dm%s\33[0m" % (fg, bg, string))
    
Red = 1
Green = 2
Yellow = 3
Blue = 4
Magenta = 5
Cyan = 6
White = 7
 
def red(string):
    return withColor(string, Red+30) # Red
def yellow(string):
    return withColor(string, Yellow+30) # Yellow

warn = red
info = yellow

rpc_jscode = """
function mkdirs(dirpath) {
    var FileClz = Java.use("java.io.File");
    var file = FileClz.$new(dirpath);
    if (!file.exists()) {
        file.mkdirs();
    }
}

function writeFileAsBase64Content(filepath, base64) {
    try {
        var FileUtilsClz = Java.use("android.os.FileUtils");
        var StringClz = Java.use('java.lang.String');
        var Base64Clz = Java.use("android.util.Base64");
        var ByteArrayInputStreamClz = Java.use("java.io.ByteArrayInputStream");
        var FileOutputStreamClz = Java.use("java.io.FileOutputStream");
        var FileClz = Java.use("java.io.File");
        var distFilepath = FileClz.$new(filepath);
        mkdirs(distFilepath.getParent());
        var javaBase64String = StringClz.$new(base64);
        var getBytesMehtod = StringClz.getBytes.overload('java.lang.String');
        var bytes = getBytesMehtod.call(javaBase64String, 'UTF-8');
        var decodeMethod = Base64Clz.decode.overload('[B', 'int');
        var originalBinary = decodeMethod.call(Base64Clz, bytes, 0);
        var bais = ByteArrayInputStreamClz.$new(originalBinary);
        if (FileUtilsClz.copy) {
            var copyMehtod = FileUtilsClz.copy.overload('java.io.InputStream', 'java.io.OutputStream');
            var fos = FileOutputStreamClz.$new(distFilepath);
            copyMehtod.call(FileUtilsClz, bais, fos);
        } else if (FileUtilsClz.copyToFile) {
            var copyMehtod = FileUtilsClz.copyToFile.overload('java.io.InputStream', 'java.io.File');
            copyMehtod.call(FileUtilsClz, bais, distFilepath);
        }
    } catch(err) {
        console.warn(err);
    }
};

function checkFile(filepath, checkLength) {
    var FileClz = Java.use("java.io.File");
    var file = FileClz.$new(filepath);
    return file.exists() && file.length() == checkLength;
};

rpc.exports = {
    write: function(filename, contentAsBase64) {
        Java.perform(function() {
            //console.log(contentAsBase64);
            writeFileAsBase64Content(filename, contentAsBase64);
        });
    },
    checkfile: function(filename, filelength) {
        var ret = false;
        Java.perform(function() {
            ret = checkFile(filename, filelength);
        });
        return ret;
    },
};

"""

def getHookerDriverHost():
    try:
        hookerDriver = io.open('../.hooker_driver', 'r', encoding= 'utf8').read()
        hookerDriver = hookerDriver.replace("-H", "").strip()
        return hookerDriver
    except Exception:
        return "-U"

class XinitFile:
    def __init__(self, filename, filepath):
        self.filename = filename
        self.filepath = filepath

    def fileData(self):
        fopen = open(self.filepath,"rb")
        data = fopen.read()
        fopen.close()
        return data
    
def readXinitFiles():
    xinitFiles = []
    if not os.path.exists("./xinit"):
        return xinitFiles
    allFiles = os.listdir("./xinit")
    for filename in allFiles:
        filepath = "./xinit/" + filename
        if os.path.isdir(filepath):
            continue
        xinitFile = XinitFile(filename, filepath)
        xinitFiles.append(xinitFile)
    return xinitFiles

def on_message(message, data):
    pass

def attach(packageName):
    online_session = None
    online_script = None
    hookerDriver = getHookerDriverHost()
    try:
        if hookerDriver != "-U":
            rdev = frida.get_device_manager().add_remote_device(hookerDriver)
        elif platform.system().find("Windows") != -1:
            warn("推荐使用linux或mac操作系统获得更好的兼容性.")
            rdev = frida.get_remote_device()
        else:
            rdev = frida.get_usb_device(1000)
        online_session = rdev.attach(packageName)
        if online_session == None:
            warn("attaching fail to " + packageName)
        online_script = online_session.create_script(rpc_jscode)
        online_script.on('message', on_message)
        online_script.load()
    except Exception:
        warn(traceback.format_exc())   
    return online_session,online_script
    

def detach(online_session):
    if online_session != None:
        online_session.detach()
 

def xinitDeploy(packageName):
    xinitFiles = readXinitFiles()
    if xinitFiles == None or len(xinitFiles) == 0:
        warn("deploying aborted. because not found any file in the path xinit.")
        return
    online_session = None
    online_script = None
    try:
        online_session,online_script = attach(packageName);
        for xinitFile in xinitFiles:
            dataBase64 = base64.b64encode(xinitFile.fileData()).decode()
            distPath = "/data/user/0/" + packageName + "/xinit/" + xinitFile.filename
            info("copying " + xinitFile.filename + " to that path " + distPath + ".")
            online_script.exports.write(distPath, dataBase64)
        info("deploying xinit finished.")
    except Exception:
        warn("deploying xinit failure.")
        warn(traceback.format_exc())  
    finally:    
        detach(online_session)
        