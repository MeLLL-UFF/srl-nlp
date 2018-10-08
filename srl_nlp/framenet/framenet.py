import collections
import distance as _dist
import logging
from typing import Dict, Union, List, Iterable, Iterator

logger = logging.getLogger(__name__)


class Lexeme:
    def __init__(self, name='', pos='', breakBefore=True, headWord=True, text=''):
        self.name = name
        self.pos = pos
        self.breakBefore = breakBefore
        self.headWord = headWord
        self.text = text

    def __repr__(self):
        return str(self)

    def __str__(self):
        return "{name}.{pos}".format(name=self.name, pos=self.pos)

    def __eq__(self, other):
        return self.name == other.name and self.pos.lower() == other.pos.lower()

    def __hash__(self):
        return (self.name, self.pos).__hash__()


class LexicalUnit:
    def __init__(self, name, pos='', status='', definition='',
                 annotation=(0, 0), idx=None, lexeme=None):
        self.name = name
        self.pos = pos
        self.status = status
        self.definition = definition
        self.annotation = annotation
        self.id = idx
        self.lexeme = lexeme

    def __repr__(self):
        return "LU('{name}.{pos}',{anot},{status})".format(name=self.name,
                                                           pos=self.pos,
                                                           anot=self.annotation,
                                                           status=self.status)

    def __str__(self):
        return "{name}.{pos}".format(name=self.name, pos=self.pos)

    def __eq__(self, other):
        return self.name == other.name and self.pos.lower() == other.pos.lower()

    def __hash__(self):
        return (self.name, self.pos).__hash__()


class Description(collections.Iterable):
    class Label(collections.Iterable):
        name = 'l'
        shortname = 'Label'

        def __init__(self, content=None, escapeHTML=False, **attribs):
            # type: (List[Union[Description.Label,str]], bool, Dict[str,str]) -> None
            if content is None:
                self.content = []
            else:
                self.content = content
            self.attribs = attribs
            self.escapeHTML = escapeHTML

        def __str__(self, escapeHTML=False):
            attr = ''.join(['%s="%s"' % item for item in self.attribs.iteritems()])
            if len(attr) > 0:
                attr = ' ' + attr
            if escapeHTML or self.escapeHTML:
                return '&lt;{name}{attr}&gt;{content}&lt;/{name}&gt;' \
                    .format(name=self.name,
                            attr=attr,
                            content=''.join(map(str, self.content)))
            else:
                return '<{name}{attr}>{content}</{name}>' \
                    .format(name=self.name,
                            attr=attr,
                            content=''.join(map(str, self.content)))

        def __len__(self):
            return sum(map(len, self.content))

        def __getitem__(self, item):
            return self.content[item]

        def __setitem__(self, item, val):
            logger.debug('Val %s' % val)
            logger.debug('Content "%s"' % self.content)
            if isinstance(item, slice):
                self.content = self.content[:item.start] + val + self.content[item.stop:]
            else:
                self[item:item] = val

        def __repr__(self):
            attr = ''.join(['%s = "%s"' % item for item in self.attribs.iteritems()])
            if len(attr) > 0:
                attr = ' ' + attr
            return '{name}(\'{desc}\'{attr})'.format(name=self.shortname,
                                                     attr=attr,
                                                     desc=''.join(map(str, self.content)))

        def __hash__(self):
            return (self.name, tuple(self.content), tuple(self.attribs.items())).__hash__()

        def add_text(self, text):
            if len(self.content) and type(self.content[-1]) == str:
                self.content[-1] = self.content[-1] + text
            else:
                self.content.append(text)

        def add_element(self, element):
            self.content.append(element)

        def set_attribs(self, **attribs):
            self.attribs = attribs

        def str_no_annotation(self):
            out = ''
            try:
                for elem in self.content:
                    if isinstance(elem, Description.Label):
                        text = elem.str_no_annotation()
                    else:
                        text = elem
                    out = out + text
            except TypeError as e:
                logger.error(str(self))
                raise e
            return out

    class FEName(Label):
        name = 'fen'
        shortname = 'FEName'

    class FEeXample(Label):
        name = 'fex'
        shortname = 'FEeXample'

    class EXample(Label):
        name = 'ex'
        shortname = 'EXample'

    class Special(Label):
        name = 'special'
        shortname = 'Special'

    class T(Special):
        name = 't'
        shortname = 'Target'

    class M(Special):
        name = 'm'

    class Ment(Special):
        name = 'ment'

    class Gov(Special):
        name = 'gov'

    class EM(Special):
        name = 'em'

    class Supp(Special):
        name = 'supp'

    class Target(Special):
        name = 'target'

    def __init__(self, escapeHTML=False):
        self.fens = set()
        self.specials = set()
        self.content = []
        self.escapeHTML = escapeHTML
        self.tags = dict()

    def add_text(self, text):
        if len(self.content) and type(self.content[-1]) == str:
            self.content[-1] = self.content[-1] + text
        else:
            self.content.append(text)

    def add_element(self, element):
        self.content.append(element)
        if isinstance(element, Description.FEName):
            self.fens.add(element)
        elif isinstance(element, Description.Special):
            self.specials.add(element)
        self.tags[element.name] = self.tags.get(element.name, [])
        self.tags[element.name].append(element)

    def get_elements(self, element_or_element_name):
        """Returns a list of elements that match element or element_name"""
        if hasattr(element_or_element_name, 'name'):
            element_name = element_or_element_name.name
        else:
            element_name = element_or_element_name
        return self.tags.get(element_name, [])

    def has_special_annotation(self):
        return len(self.specials) > 0

    def has_fe_annotation(self):
        return len(self.fens) > 0

    def get_fens(self):
        return self.fens

    def __iter__(self):
        # type: () -> Iterator[Union[Description.Label, str]]
        return self.content.__iter__()

    def __contains__(self, element):
        return element in self.fens or element in self.specials

    def __str__(self, escapeHTML=False):
        if escapeHTML or self.escapeHTML:
            return '&lt;def-root&gt;%s&lt;/def-root&gt;' % (''.join(map(str, self.content)))
        else:
            return '<def-root>%s</def-root>' % (''.join(map(str, self.content)))

    def __repr__(self):
        return str(self)


class Frame:
    class Element:
        def __init__(self, name='', abbrev='', definition='',
                     fgColor='black', bgColor='white', isCore=True, semanticType='', idx=None):
            self.name = name
            self.abbrev = abbrev
            self.definition = definition  # type: Union[str, Description]
            self.fgColor = fgColor
            self.bgColor = bgColor
            self.isCore = isCore
            self.semanticType = semanticType
            self.id = idx

        def __eq__(self, other):
            if type(other) == str:  # allow comparison with string
                other_name = other
            else:
                other_name = other.name
            return self.name == other_name  # and self.abbrev == other.abbrev

        def __hash__(self):
            return self.name.__hash__()
            # return (self.name, self.abbrev).__hash__()

        def __str__(self):
            # return '<Frame "%s" %s>' %(self.name, dir(self))
            return '<Frame Element "%s"[%s]>' % (self.name, self.abbrev)

        def __repr__(self):
            return str(self)

    class Relation(collections.Iterable):
        def __init__(self, name, frames=None):
            # type: (str, List[Frame]) -> None
            self.name = name
            if frames is None:
                self.frames = []
            else:
                self.frames = frames

        def __iter__(self):
            # type: () -> Iterator[Union[Frame, str]]
            return self.frames.__iter__()

        def __str__(self):
            # return '<Frame "%s" %s>' %(self.name, dir(self))
            frame_names = map(lambda x: x.name, self.frames)
            return '%s: %s' % (self.name, str(frame_names)[1:-1])

        def __repr__(self):
            frame_names = map(lambda x: x.name, self.frames)
            return '{%s}' % str(frame_names)[1:-1]

        def __eq__(self, other):
            if type(other) == str:
                return self.name == other
            else:
                return self.name == other.name

    def __init__(self, name='', description='', core_fes=None,
                 peripheral_fes=None, lus=None, idx=None, **relations):
        # type: (str, str, List[Frame.Element], List[Frame.Element], List[LexicalUnit], Union[int, str], Dict[str, Relation]) -> None
        assert name is not None  # None type is not an acceptable name
        self.name = name
        self.description = description

        if core_fes is None:
            self.coreFEs = []
        else:
            self.coreFEs = core_fes

        if peripheral_fes is None:
            self.peripheralFEs = []
        else:
            self.peripheralFEs = peripheral_fes

        if lus is None:
            self.LUs = []
        else:
            self.LUs = lus

        self.id = idx
        self.relations = relations

    def hasFEinCore(self, fe):
        """Check if fe is in the frame as a core Frame Element"""
        return fe in self.coreFEs

    def hasFEnotInCore(self, fe):
        """Check if fe is in the frame as a peripheral Frame Element"""
        return fe in self.peripheralFEs

    def __str__(self):
        # return '<Frame "%s" %s>' %(self.name, dir(self))
        return '<Frame "%s">' % self.name

    def _in_transitive_closure(self, relation_name, other, investigated=None):
        """Checks if a given frame, other, can be reached by a transitive closure of the relation."""
        if investigated is None:
            investigated = []
        investigated.append(self)
        for relation in self.relations.values():
            if relation.name == relation_name:
                if other in relation.frames:
                    return True
                else:
                    for child in relation.frames:
                        if child not in investigated:
                            if self._in_transitive_closure(relation_name, other, investigated):
                                return True
        return False

    def in_transitive_closure(self, relation_name, other):
        """
        Checks if a given frame, other, can be reached by a transitive closure of
        the relation.
        """
        return self._in_transitive_closure(relation_name, other)

    def __hash__(self):
        # The way that relation references works need this hash to point to the frame's name hash
        return self.name.__hash__()

    def __eq__(self, other):
        # type: (Union[str, Frame]) -> bool
        """
        Two Frames are equal if they have the same name, the same Core Frame Elements,
        and the same Peripheral Frame elements.

        Args:
            other:
        """
        if other is None:
            return self is None
        if isinstance(other, str):
            return self.name == other

        eq_core = [fe in other.coreFEs for fe in self.coreFEs] + \
                  [fe in self.coreFEs for fe in other.coreFEs]
        eq_peripheral = [fe in other.peripheralFEs for fe in self.peripheralFEs] + \
                        [fe in self.peripheralFEs for fe in other.peripheralFEs]

        criteria = [self.name == other.name, ] + eq_core + eq_peripheral
        return reduce(lambda x, y: x and y, criteria)

    def __repr__(self):
        return str(self)


class Net(collections.Iterable):
    _word_distances = {'levenshtein': lambda x, y: _dist.levenshtein(x, y, normalized=True),
                       # 'hamming': distance.hamming #the two strings must have the same length
                       'jaccard': _dist.jaccard,
                       'sorensen': _dist.sorensen}

    def __init__(self, frames):
        """
        FrameNet python API

        Args:
            frames: A list of Frames or a dictionary where the names are the keys
        """
        if type(frames) != dict:  # if the user passes a list of frames instead of a dict then convert it
            frames = {frame.name: frame for frame in frames}
        self.frames = frames  # type: Dict[str, Frame]
        self.framesByID = dict([(frame.id, frame) for frame in frames.values()])  # type: Dict[int, Frame]
        for frame in frames.itervalues():
            self._update_frame_references(frame)
        self._fes = dict()
        self._fes2frames = dict()
        for frame in self:
            for fe in frame.coreFEs + frame.peripheralFEs:
                self._fes[fe.name] = self._fes.get(fe.name, fe)
                self._fes2frames[fe] = self._fes2frames.get(fe, [])
                self._fes2frames[fe].append(frame)

    def _update_frame_references(self, frame):
        """Uses the self.frames dict to replace the strings representing Frames by actual Frames"""

        def get_rel(frame_name):
            out_frame = self.frames.get(frame_name, None)
            if out_frame is not None:
                return out_frame
            else:
                logger.warning('Relation pointing to not existent Frame "{}"'.format(frame_name))

        for relation in frame.relations.itervalues():
            relation.frames = [f for f in map(get_rel, relation.frames) if f is not None]

    def __iter__(self):
        return self.frames.itervalues()

    def __getitem__(self, item):
        """Returns the Frames in the FrameNet by name or id, if item is a name or integer
           If item is a slice, then:

           self[word:qtd] = self.getMostSimilarFrames(word, qtd)
           self[word:qtd:distance] = self.getMostSimilarFrames(word, qtd, distance = distance)
                distace is a string
           self[word:qtd:threshold] = self.getMostSimilarFrames(word, qtd, threshold = threshold)
                threshold is an float in the interval [0, 1.0]
        """
        if type(item) == slice:
            token = item.start
            limit = item.stop
            extra = item.step
            if extra:
                if type(extra) == str:
                    return self.get_most_similar_frames(token, limit, distance=extra)
                else:
                    return self.get_most_similar_frames(token, limit, threshold=extra)
            else:
                return self.get_most_similar_frames(token, limit)
        else:
            frame = self.frames.get(item, None)
            if frame is None:
                frame = self.framesByID.get(item, None)
                if frame is None:
                    raise KeyError(
                        '\'{item}\' is not a valid Frame name or id in this FrameNet version'.format(item=item))

            return frame

    def get_most_similar_frames(self, word, qtd=3, threshold=1, distance='levenshtein'):
        """
        Return an ordered list of the most similar Frames using the specified distance:

        Implemented distances:
            'levenshtein' : the minimum number of single-character edits
            'jaccard'     : the size of the intersection divided by the size of
                            the union of two label sets
            'sorensen'    : (F1-score) 

        self.getMostSimilarFrames(str, int, float, string) ->
                    [ (socore1, Frame1), ..., (socoreN, FrameN)] # N <= qtd
        """
        top_values = []
        metric = self._word_distances[distance]

        def distance(obj):
            return metric(obj.name, word)

        for frame in self:
            score = min(map(distance, frame.LUs + [frame]))
            if score <= threshold:
                pos = 0
                for other_score, _ in top_values:
                    if score > other_score:
                        pos = pos + 1
                    else:
                        break
                top_values.insert(pos, (score, frame))
                if len(top_values) > qtd:
                    top_values.pop()
        return top_values

    def __len__(self):
        """Number of Frames in the Network"""
        return len(self.frames)

    @property
    def fe_names(self):
        """
        Returns: The list of all Frame Element names
        """
        return set(self._fes.keys())

    @property
    def frame_names(self):
        """
        Returns: The list of all Frame names
        """
        return set(self.frames.keys())

    def get_frame_element(self, name):
        """
        Returns:
            The Frame Elements in the FrameNet by name
        """
        try:
            return self._fes[name]
        except KeyError:
            raise KeyError('\'{item}\' is not a valid Frame Element name in this FrameNet'.format(item=name))

    def get_frame_element_frames(self, fe, core_fes=True, peripheral_fes=True):
        """Get all frames where the given fe is a Frame Element
        
        coreFEs: boolean value, if set True then Frames where fe is a core element will be returned
        peripheralFEs: boolean value, if set True then Frames where fe is a non-core element will be returned
        
        Returns a list of frames
        """
        if not isinstance(fe, Frame.Element):
            fe = self._fes[fe]
        frames = self._fes2frames[fe]
        if (not core_fes) or (not peripheral_fes):
            if (not core_fes) and (not peripheral_fes):
                return []
            elif core_fes:
                return filter(lambda frame: frame.hasFEinCore(fe),
                              frames)
            else:
                return filter(lambda frame: frame.hasFEnotInCore(fe),
                              frames)
        return frames

    def __str__(self):
        return '<FrameNet, %d frames>' % len(self)

    def __repr__(self):
        return str(self)
