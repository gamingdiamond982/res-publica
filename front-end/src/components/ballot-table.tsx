import React, { PureComponent } from "react";
import { VoteAndBallots, Ballot, Vote, RateOptionsBallot } from "../model/vote";
import { sortBy } from "../model/util";
import { Table, TableHead, TableCell, Paper, TableRow } from "@mui/material";

function getOptionScores(ballot: Ballot, vote: Vote): { optionId: string, rating: number }[] {
    if ('ratingPerOption' in ballot) {
        return ballot.ratingPerOption;
    } else if ('optionRanking' in ballot) {
        return vote.options.map(opt => ({ optionId: opt.id, rating: ballot.optionRanking.indexOf(opt.id) + 1}));
    } else {
        return vote.options.map(opt => ({ optionId: opt.id, rating: ballot.selectedOptionId === opt.id ? 1 : 0 }));
    }
}

function canonicalizeBallot(ballot: Ballot, vote: Vote): RateOptionsBallot {
    return {
        id: ballot.id,
        timestamp: ballot.timestamp,
        ratingPerOption: sortBy(getOptionScores(ballot, vote), x => x.optionId)
    };
}

function renderTableHeader(vote: Vote): string[] {
    return [
        "Ballot ID",
        "Timestamp",
        ...sortBy(vote.options, x => x.id).map(x => x.id)
    ];
}

function renderTableBody(voteAndBallots: VoteAndBallots): string[][] {
    let canonicalizedBallots = voteAndBallots.ballots.map(
        ballot => canonicalizeBallot(ballot, voteAndBallots.vote));
    return canonicalizedBallots.map(ballot => [
        ballot.id || "",
        ballot.timestamp ? new Date(ballot.timestamp * 1000).toUTCString() : "",
        ...ballot.ratingPerOption.map(({ rating }) => rating.toString())
    ]);
}

/**
 * Generates a CSV file from a vote and its ballots.
 * @param voteAndBallots A vote and its ballots.
 */
export function ballotsToCsv(voteAndBallots: VoteAndBallots): string {
    let contents = [
        renderTableHeader(voteAndBallots.vote),
        ...renderTableBody(voteAndBallots)
    ];
    return contents.map(row => row.map(cell => `"${cell}"`).join(',')).join('\n');
}

type Props = {
    voteAndBallots: VoteAndBallots;
};

/**
 * A table that visualizes all ballots.
 */
class BallotTable extends PureComponent<Props> {
    render() {
        let vote = this.props.voteAndBallots.vote;

        return <Paper style={{maxWidth: "80vw", overflowX: "scroll"}}>
            <Table>
                <TableHead>
                    {renderTableHeader(vote).map(x => <TableCell>{x}</TableCell>)}
                </TableHead>
                {renderTableBody(this.props.voteAndBallots).map(row =>
                    <TableRow>{row.map(cell =><TableCell>{cell}</TableCell>)}</TableRow>)}
            </Table>
        </Paper>;
    }
}

export default BallotTable;
