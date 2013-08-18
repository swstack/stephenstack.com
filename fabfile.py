from fabric.api import run, env, local, cd

env.hosts = ['stephenstack.com']
env.user = 'stephft5'


def deploy():
    with cd('~/projects/stephenstack.com.v2'):
        run('git fetch -p')
        run('git merge origin/master')
