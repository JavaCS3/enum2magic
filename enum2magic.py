#!/usr/bin/python
# 
# @author: charles wei
# @version: 1.9.5
# @date: 2015-01-29

import sys

class Parser(object):
    """ This parser converts C-Enum syntax to Magic Number syntax"""
    IDLE           = 0
    BEGIN_HEADER   = 1
    PARSING_HEADER = 2
    BEGIN_ENUM     = 3
    PARSING_ENUM   = 4

    def __init__(self, filename):
        super(Parser, self).__init__()
        self.current_state = Parser.IDLE
        self.filename = filename
        self.counter = 0
        self.target_file = None
        self.event_table = {
            Parser.IDLE           : self.on_idle,
            Parser.BEGIN_HEADER   : self.on_begin_header,
            Parser.PARSING_HEADER : self.on_header,
            Parser.BEGIN_ENUM     : self.on_begin_enum,
            Parser.PARSING_ENUM   : self.on_enum
        }
        self.config = {
            'target_name'    : '',
            'target_template': '{element} = {value}',
            'ignore_prefix'  : '',
        }

    def _transition(self, line):
        state = self.current_state

        if state == Parser.IDLE and line.startswith('---'):
            self.current_state = Parser.BEGIN_HEADER

        elif (state == Parser.PARSING_HEADER or state == Parser.BEGIN_HEADER) and line.startswith('---'):
            self.current_state = Parser.IDLE

        elif state == Parser.BEGIN_HEADER:
            self.current_state = Parser.PARSING_HEADER

        elif state == Parser.IDLE and line.find('{') > -1:
            self.current_state = Parser.BEGIN_ENUM

        elif (state == Parser.PARSING_ENUM or state == Parser.BEGIN_ENUM) and line.find('}') > -1:
            self.current_state = Parser.IDLE

        elif state == Parser.BEGIN_ENUM:
            self.current_state = Parser.PARSING_ENUM

        else:
            pass

    def _fire_events(self, line):
        try:
            self.event_table[self.current_state](line)
        except Exception, e:
            print '*** WARNING:' , e , ' ***'

    def on_idle(self, line):
        pass

    def on_begin_header(self, line):
        print '- Reading Config'

    def on_header(self, line):
        # print '%-35s => on_header' % line
        colon_ind = line.find(':')
        if colon_ind < 0: return
        key   = line[:colon_ind].strip()
        value = line[colon_ind+1:].strip()
        if key in self.config:
            self.config[key] = value
            print '-- {key:<15} -> {value}'.format(key=key, value=value)

    def _get_target_file(self):
        if self.target_file == None and self.config['target_name']:
            self.target_file = open(self.config['target_name'], 'w')
        return self.target_file

    @staticmethod
    def _break_down(line):
        value   = None
        comment = ''

        # get comment
        comment_ind = line.find('//')
        if comment_ind > -1:
            comment = line[comment_ind:]
            line = line[:comment_ind]
        line = line.strip(', ')
        # get value
        equal_ind = line.find('=')
        if equal_ind > -1:
            value = int(line[equal_ind+1:])
            line = line[:equal_ind]
        line = line.strip(', ')
        # get content
        return {'element': line, 
                'value'  : value, 
                'comment': comment}

    def _render(self, **kwargs):
        return self.config['target_template'].format(**kwargs)

    def on_begin_enum(self, line):
        print '- Reading Enum'

    def on_enum(self, line):
        f = self._get_target_file()
        if f :
            pack = Parser._break_down(line)
            pack['element'] = pack['element'].lstrip(self.config['ignore_prefix'])
            self.counter = self.counter if pack['value'] is None else pack['value']

            if pack['element']:
                data = self._render(element = pack['element'],\
                                    value   = self.counter,\
                                    comment = pack['comment'])
                self.counter += 1
            else:
                data = pack['comment']
            f.write(data + '\n')

    def parse(self):
        with open(self.filename) as f:
            for line in f:
                line = line.strip()
                self._transition(line)
                self._fire_events(line)
                # print '%-35s => state: %s' % (line, self.current_state)

        if self.target_file:
            self.target_file.close()

if __name__ == '__main__':
    fname = 'sample'
    if len(sys.argv) == 2: fname = sys.argv[1]
    try:
        print '=== Begin Parsing: %s ===' % fname
        Parser(fname).parse()
    except Exception, e:
        print '*** ERROR:' , e , ' ***'
    finally:
        print '=== End Parsing: %s ===' % fname
