from ftplib import FTP
from File import File
from ftplib import error_perm

# https://www.zhangshengrong.com/p/24Nj0OP1B7/
class Aftp:
	def __init__(self, host, port, user, passwd, ignoreds=[]):
		self.host = host
		self.port = port
		self.user = user
		self.passwd = passwd
		self.ignoreds = ignoreds
		self.baseDir = ""

		self.ftp = FTP()
		self.ftp.encoding = "utf-8"

		print("ignored list: "+str(ignoreds))
	
	def open(self):
		print(f"connect to {self.host}:{self.port}")

		self.ftp.connect(self.host, self.port, timeout=5000)
		self.ftp.login(self.user, self.passwd)

		print(self.ftp.getwelcome())
	
	def close(self):
		self.ftp.close()
		print(f"disconnected from {self.host}:{self.port}")

	def syncDir(self, local, remote):
		folder = File(local)

		if not folder.exists:
			raise FileNotFoundError(f"'{folder.path}' not found")

		if folder.isFile:
			raise IsADirectoryError(f"'{folder.path}' is not a directory")

		if self.isIgnored(folder):
			return

		self.ftp.cwd(remote)
		print(f"cd into: {self.ftp.pwd()}")

		currFiles = self.ftp.nlst()

		print("start to upload files")

		for sf in folder:
			remoteSf = remote+"/"+sf.name

			if self.isIgnored(sf):
				continue

			if sf.isFile:
				self.uploadFile(sf.path, remoteSf)
			if sf.isDirectory:
				if not sf.name in currFiles:
					print(f"create dir: {sf.name}    |"+sf.name+"|"+str(currFiles))
					self.ftp.mkd(sf.name)
				self.syncDir(sf.path, remoteSf)

		print("start to delete files")

		for df in currFiles:
			remoteSf = remote+"/"+df

			if self.isIgnored(sf):
				continue

			if not df in folder:
				self.delete(remoteSf)

		self.ftp.cwd("..")
		print(f"cd back to: {self.ftp.pwd()}")

	def uploadFile(self, local, remote):
		file = File(local)

		if not file.exists:
			raise FileNotFoundError(f"'{file.path}' not found")

		if file.isDirectory:
			raise IsADirectoryError(f"'{file.path}' is not a file")

		if self.isIgnored(file):
			return
		
		print(f"upload {file.relativePath()} => {remote}", end="")

		fd = open(local, 'rb')
		self.ftp.storbinary('STOR '+remote, fd)

		fd.close()

		print("   OK")
	
	def delete(self, remote):
		try:
			print(f"delete {remote}", end="")
			self.ftp.delete(remote)
			print("")
		except Exception:
			self.ftp.cwd(remote)
			print(f" | cd into: {self.ftp.pwd()}")

			currFiles = self.ftp.nlst()

			for df in currFiles:
				remoteSf = remote+"/"+df
				self.delete(remoteSf)
			
			self.ftp.cwd("..")
			print(f"cd back to: {self.ftp.pwd()}")

			print(f"rmd {remote}")
			self.ftp.rmd(remote)
	
	def isIgnored(self, file):
		relPath = file.relativePath(self.baseDir)

		#print("___"+relPath+"|"+file.path)

		# for i in self.ignoreds:
		# 	if relPath

		if relPath in self.ignoreds:
			print(f"ignore {relPath}")
			return True

		return False

	def upload(self, local, remote=""):
		file = File(local)

		self.baseDir = file

		if not file.exists:
			raise FileNotFoundError(f"'{file.path}' not found")

		if file.isFile:
			self.uploadFile(file.path, remote)
		
		if file.isDirectory:
			self.syncDir(file.path, remote)
		
		self.baseDir = ""

	def __enter__(self):
		self.open()

		return self

	def __exit__(self, exc_type, exc_value, traceback):
		self.close()
