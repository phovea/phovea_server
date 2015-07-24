from server import run, application

if __name__ == '__main__':
  print 'run as standalone version'
  run()
else:
  print 'run as embedded version'