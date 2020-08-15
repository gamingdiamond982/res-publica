#!/usr/bin/env python3

import time
import os
from Crypto.Hash import SHA3_256
from pathlib import Path
from typing import Any, Dict, List
from helpers import read_json, write_json
from authentication import RegisteredDevice


VoteId = str
BallotId = str
Vote = Any
VoteAndBallots = Any
Ballot = Any


def is_vote_active(vote: VoteAndBallots) -> bool:
    return vote['vote']['deadline'] > time.monotonic()


class VoteIndex(object):
    """Keeps track of votes."""
    def __init__(self, index_path: str, votes: Dict[VoteId, VoteAndBallots], vote_secrets: Dict[VoteId, str]):
        self.index_path = index_path
        self.votes = votes
        self.vote_secrets = vote_secrets

    def get_active_votes(self, device: RegisteredDevice) -> List[VoteAndBallots]:
        """Gets all currently active votes."""
        return [
            self.prepare_for_transmission(vote, device)
            for vote in self.votes.values()
            if is_vote_active(vote)
        ]

    def get_vote(self, vote_id: VoteId, device: RegisteredDevice) -> Vote:
        """Gets a vote."""
        return self.prepare_for_transmission(self.votes[vote_id], device)

    def cast_ballot(self, vote_id: VoteId, ballot: Ballot, device: RegisteredDevice) -> BallotId:
        """Casts a ballot."""
        ballot_id = self.get_ballot_id(vote_id, device)
        vote = self.votes[vote_id]
        vote['ballots'] = [ballot for ballot in vote['ballots'] if ballot['id'] != ballot_id]
        ballot['id'] = ballot_id
        vote['ballots'].append(ballot)
        return ballot_id

    def prepare_for_transmission(self, vote: VoteAndBallots, device: RegisteredDevice) -> VoteAndBallots:
        """Prepares a vote for transmission."""
        if is_vote_active(vote):
            result = {
                'vote': vote['vote'],
                'ballots': []
            }
            ballot_id = self.get_ballot_id(device, vote['vote']['id'])
            for ballot in vote['ballots']:
                if ballot['id'] == ballot_id:
                    result['ownBallot'] = ballot
                    break

            return result
        else:
            return vote

    def get_ballot_id(self, vote_id: VoteId, device: RegisteredDevice) -> BallotId:
        """Gets a user's ballot ID for a particular vote."""
        if not self.vote_secrets.get(vote_id):
            raise ValueError(f'Vote with ID {vote_id} either does not exist or is no longer active.')

        hash_obj = SHA3_256.new(device.user_id.encode('utf-8'))
        hash_obj.update(self.vote_secrets[vote_id.encode('utf-8')])
        return hash_obj.hexdigest()

    def write_index(self):
        """Writes the index itself to disk."""
        write_json(self.vote_secrets, self.index_path)

    def write_vote(self, vote: VoteAndBallots):
        """Writes a vote to disk."""
        vote_id = vote['vote']['id']
        write_json(vote, vote_id_to_path(self.index_path, vote_id))


def vote_id_to_path(index_path: str, vote_id: VoteId) -> str:
    """Takes a vote ID and an index path and turns it into a path to the location
       where the vote's data is stored."""
    return os.path.join(os.path.dirname(index_path), 'votes', vote_id)


def read_or_create_vote_index(path: str) -> VoteIndex:
    """Reads a vote index from a file; creates a blank vote index if
       the file does not exist."""
    try:
        vote_secrets = read_json(path)
    except FileNotFoundError:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        return VoteIndex(path, {}, {})

    votes = {
        vote_id: read_json(vote_id_to_path(path, vote_id))
        for vote_id in vote_secrets.keys()
    }

    return VoteIndex(path, votes, vote_secrets)